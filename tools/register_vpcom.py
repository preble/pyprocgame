import os
import sys
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
#from procgame import fakepinproc
import pinproc
import win32com
import pythoncom
import win32com.server.util
from win32com.server.util import wrap, unwrap
import thread
import yaml
from procgame import *

class ISettings:
	_public_methods_ = []
	_public_attrs_ = [ 	'Value']

	def Value(self, item, item2):
		return True
	def SetValue(self, item, item2):
		return True

class IGames:
	_public_methods_ = []
	_public_attrs_ = [ 	'Settings']

	def Settings(self):
		settings = ISettings()	
		Settings = wrap( settings )
		return Settings

	def SetSettings(self):
		settings = ISettings()	
		Settings = wrap( settings )
		return Settings

IID_IController = pythoncom.MakeIID('{CE9ECC7C-960F-407E-B27B-62E39AB1E30F}')

class Controller:
	"""Main Visual Pinball COM interface class."""
	_public_methods_ = [ 	'Run',
				'Stop',
				'PrintGlobal']
	_reg_progid_ = "VPinMAME.Controller"
	_reg_clsid_ = "{F389C8B7-144F-4C63-A2E3-246D168F9D39}"
	_public_attrs_ = [ 	'Version',
				'GameName', 
				'Games', 
				'SplashInfoLine',
				'ShowTitle',
				'ShowFrame',
				'ShowDMDOnly',
				'HandleMechanics',
				'HandleKeyboard',
				'DIP',
				'Switch',
				'Mech',
				'Pause',
				'ChangedSolenoids',
				'ChangedGIStrings',
				'ChangedLamps',
				'GetMech']
				
	_readonly_attrs_ = [ 	'Version', 
				'ChangedSolenoids',
				'ChangedLamps',
				'ChangedGIStrings',
				'GetMech']
	
	Version = "22222222"
	ShowTitle = None
	ShowFrame = False
	ShowDMDOnly = False
	HandleKeyboard = False
	DIP = False
	GameName = "Game name"
	switch = [True]*128
	lastSwitch = None
	Pause = None
	
	game = None
	last_lamp_states = []
	last_coil_states = []
	last_gi_states = []
	
	HandleMechanics = True

	# Need to overload this method to tell that we support IID_IServerWithEvents
	def _query_interface_(self, iid):
		""" Return this main interface if the IController class is queried. """
		if iid == IID_IController:
			return win32com.server.util.wrap(self)
	
        def PrintGlobal(self):
		""" Unused by pyprocgame. """
        	return True
        
	def Run(self):
		""" Figure out which game to play based on the contents of the 
		vp_game_map_file. """

		vp_game_map_file = config.value_for_key_path(keypath='vp_game_map_file', default='/.')
		vp_game_map = yaml.load(open(vp_game_map_file, 'r'))
		game_class = vp_game_map[self.GameName]['kls']
		game_path = vp_game_map[self.GameName]['path']
		yamlpath = vp_game_map[self.GameName]['yaml']

		rundir = vp_game_map['rundir']
		os.chdir(rundir)

		#game_config = yaml.load(open(yamlpath, 'r'))
		#machine_type = game_config['PRGame']['machineType']
		#self.game = None
		
		klass = util.get_class(game_class,game_path)
	 	#self.game = klass(machine_type)
	 	self.game = klass()
		self.game.log("GameName: " + str(self.GameName))
		self.game.log("SplashInfoLine: " + str(self.SplashInfoLine))
		self.game.yamlpath = yamlpath
	 	self.last_lamp_states = self.getLampStates()
	 	self.last_coil_states = self.getCoilStates()
		self.game.setup()

		# Initialize switches.  Call SetSwitch so it can invert
		# normally closed switches as appropriate.
		for i in range(0,120):
			self.SetSwitch(i, False)
		thread.start_new_thread(self.game.run_loop,())

		return True
		
	def Stop(self):
		""" Currently unused. """
		
		#TODO: Figure out a way to kill the run_loop thread.
		return True

	def Games(self, rom_name):
		""" Return the IGames interface, by wrapping the object. """
		games = IGames()
		wrapped_games = wrap (games)
		return wrapped_games

	def SetGames(self, rom_name):
		""" Return the IGames interface, by wrapping the object. """
		games = IGames()
		wrapped_games = wrap (games)
		return wrapped_games
		
	def Switch(self, number):
		""" Return the current value of the requested switch. """
		if number != None: self.lastSwitch = number
		return self.switch[self.lastSwitch]
				
	def SetSwitch(self, number, value):
		""" Set the value of the requested switch. """

		# All of the 'None' logic is error handling for unexpected
		# cases when None is passed in as a parameter.  This seems to
		# only happen with the original VP scripts when the switch data
		# is corrupted by making COM calls into this object.  This
		# appears to be a pywin32 bug.

		if value == None: return self.Switch(number)
		if number == None: return self.Switch(number)
		if number != None: self.lastSwitch = number
		self.switch[self.lastSwitch] = value
		
		if self.lastSwitch < 10:
			prNumber = self.VPSwitchDedToPRSwitch(self.lastSwitch)
		elif self.lastSwitch < 110:
			prNumber = self.VPSwitchMatrixToPRSwitch(self.lastSwitch)
		elif self.lastSwitch < 120:
			prNumber = self.VPSwitchFlipperToPRSwitch(self.lastSwitch)
		else: prNumber = 0

		if not self.game.switches.has_key(prNumber): return False
		if self.game.switches[prNumber].type == 'NC': 
			self.AddSwitchEvent(prNumber, not value)
		else: self.AddSwitchEvent(prNumber, value)

		return True

	def AddSwitchEvent(self, prNumber, value):
		""" Add the incoming VP switch event into the p-roc emulator. """
		# VP doesn't have a concept of bouncing switches; so send
		# both nondebounced and debounced for each event to ensure
		# switch rules for either event type will be processed.
		if value:
			self.game.proc.add_switch_event(prNumber, pinproc.EventTypeSwitchClosedNondebounced)
			self.game.proc.add_switch_event(prNumber, pinproc.EventTypeSwitchClosedDebounced)
		else:
			self.game.proc.add_switch_event(prNumber, pinproc.EventTypeSwitchOpenNondebounced)
			self.game.proc.add_switch_event(prNumber, pinproc.EventTypeSwitchOpenDebounced)
		
	def VPSwitchMatrixToPRSwitch(self, number):
		""" Helper method to find the P-ROC number of a matrix switch. """
		vpNumber = ((number / 10)*8) + ((number%10) - 1)
		vpIndex = vpNumber / 8
		vpOffset = vpNumber % 8 + 1
		if vpIndex < 10:
			switch = 'S' + str(vpIndex) + str(vpOffset)
			return pinproc.decode(self.game.machine_type,switch)
		else: return number

			
	def VPSwitchFlipperToPRSwitch(self, number):
		""" Helper method to find the P-ROC number of a flipper switch. """
		vpNumber = number - 110
		switch = 'SF' + str(vpNumber)
		return pinproc.decode(self.game.machine_type, switch)
		
	def VPSwitchDedToPRSwitch(self, number):
		""" Helper method to find the P-ROC number of a direct switch. """
		vpNumber = number
		switch = 'SD' + str(vpNumber)
		return pinproc.decode(self.game.machine_type, switch)
		
	def Mech(self, number):
		""" Currently unused.  Game specific mechanism handling will
		be called through this method. """
		return True
		
	def SetMech(self, number):
		""" Currently unused.  Game specific mechanism handling will
		be called through this method. """
		return True
		
	def GetMech(self, number):
		""" Currently unused.  Game specific mechanism handling will
		be called through this method. """
		return 0
		
	def ChangedSolenoids(self):
		""" Return a list of changed coils. """
		coils = self.getCoilStates()
		changedCoils = []
		
		already=False
		if len(self.last_coil_states) > 0:
			for i in range(0,len(coils)):
				if coils[i] != self.last_coil_states[i]:
					if not already:
						changedCoils += [(0,True)]
						already = True
					changedCoils += [(i,coils[i])]
				
		self.last_coil_states = coils
		return changedCoils
		
	def ChangedLamps(self):
		""" Return a list of changed lamps. """
		lamps = self.getLampStates()
		changedLamps = []
		
		if len(self.last_lamp_states) > 0:
			for i in range(0,len(lamps)):
				if lamps[i] != self.last_lamp_states[i]:
					changedLamps += [(i,lamps[i])]
				
		self.last_lamp_states = lamps
		return changedLamps

	def ChangedGIStrings(self):
		""" Return a list of changed GI strings. """
		gi = self.getGIStates()
		changedGI = []

		if len(self.last_gi_states) > 0:
			for i in range(0,len(gi)):
				if gi[i] != self.last_gi_states[i]:
					changedGI += [(i,gi[i])]

		self.last_gi_states = gi
		return changedGI
			
	def getGIStates(self):
		""" Gets the current state of the GI strings. """
		vpgi = [False]*5
	
		for i in range(0,5):
			numStr = 'G0' + str(i+1)
			prNumber = pinproc.decode(self.game.machine_type, numStr)
			vpgi[i] = self.game.proc.drivers[prNumber].curr_state
			
		return vpgi
		
	def getLampStates(self):
		""" Gets the current state of the lamps. """
		vplamps = [False]*90
	
		for i in range(0,64):
			vpNum = (((i/8)+1)*10) + (i%8) + 1
			vplamps[vpNum] = self.game.proc.drivers[i+80].curr_state
			
		return vplamps
		
	def getCoilStates(self):
		""" Gets the current state of the coils. """

		pycoils = self.game.proc.drivers
		vpcoils = [False]*64
	
		for i in range(0,len(vpcoils)):
			if i<=28: vpcoils[i] = pycoils[i+39].curr_state
			elif i<33: vpcoils[i] = False # Unused?

			# Use the machine's Hold coils for the VP flippers
			# since they stay on until the button is released
			elif i == 34: vpcoils[i] = pycoils[pinproc.decode(self.game.machine_type, "FURH")].curr_state
			elif i == 36: vpcoils[i] = pycoils[pinproc.decode(self.game.machine_type, "FULH")].curr_state
			elif i<44:
				if self.game.machine_type == pinproc.MachineTypeWPC95:
					vpcoils[i] = pycoils[i+31].curr_state
				else: vpcoils[i] = pycoils[i+107].curr_state
			elif i == 46: vpcoils[i] = pycoils[pinproc.decode(self.game.machine_type, "FLRH")].curr_state
			elif i == 48: vpcoils[i] = pycoils[pinproc.decode(self.game.machine_type, "FLLH")].curr_state
			else: vpcoils[i] = pycoils[i+108].curr_state

		return vpcoils		
			
		
def Register(pyclass=Controller, p_game=None):
	""" Registration code for the Visual Pinball COM interface for pyprocgame."""
	pythoncom.CoInitialize()
	from win32com.server.register import UseCommandLine
	UseCommandLine(pyclass)
	
# Run the registration code by default.  Using the commandline param
# "--unregister" will unregister this COM object.
if __name__=='__main__':
	Register(Controller)
