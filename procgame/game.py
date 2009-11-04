import os
import pinproc
import Queue
import yaml
import time
import copy
import re

class const:
	"""From http://code.activestate.com/recipes/65207/"""
	def __setattr__(self, attr, value):
		if hasattr(self, attr):
			raise ValueError, 'const %s already has a value and cannot be written to' % attr
		self.__dict__[attr] = value

class Mode(object):
	"""Abstraction of a game mode to be subclassed by the game
	programmer.
	
	Modes are essentially a collection of switch even thandlers.  
	Active modes are held in the GameController object's modes
	ModeQueue, which dispatches event notifications to modes in
	order of priority (highest to lowest).  If a higher priority
	mode's switch event handler method returns True, the event
	is not passed down to lower modes.
	
	Switch event handlers are detected when Mode.__init__() is
	called by the subclass.  Various switch event handler formats
	are recognized:
	
	sw_switchName_open(self, sw) -- called when a switch (named 
	                                switchName) is opened
	sw_switchName_closed(self, sw) -- closed variant of the above
	sw_switchName_open_for_1s(self, sw)
	  -- called when switchName has been open continuously for
	     one second
	sw_switchName_closed_for_2s(self, sw)
	sw_switchName_closed_for_100ms(self, sw)
	sw_switchName_open_for_500ms(self, sw)
	  -- variants of the above
	
	Modes can be programatically configured using add_switch_handler().
	"""
	def __init__(self, game, priority):
		super(Mode, self).__init__()
		self.game = game
		self.priority = priority
		self.__accepted_switches = []
		self.__delayed = []
		self.__scan_switch_handlers()
	
	def __scan_switch_handlers(self):
		# Format: sw_popperL_open_for_200ms(self, sw):
		handler_func_re = re.compile('sw_(?P<name>[a-zA-Z0-9]+)_(?P<state>open|closed|active|inactive)(?P<after>_for_(?P<time>[0-9]+)(?P<units>ms|s))?')
		for item in dir(self):
			m = handler_func_re.match(item)
			if m == None:
				continue
			seconds = None
			if m.group('after') != None:
				seconds = float(m.group('time'))
				if m.group('units') == 'ms':
					seconds /= 1000.0

			handler = getattr(self, item)
			
			self.add_switch_handler(name=m.group('name'), event_type=m.group('state'), delay=seconds, handler=handler)
	
	def add_switch_handler(self, name, event_type, delay, handler):
		"""Programatically configure a switch event handler.
		
		Keyword arguments:
		name       -- valid switch name
		event_type -- 'open','closed','active', or 'inactive'
		delay      -- float number of seconds that the state should be held 
		              before invoking the handler, or None if it should be
		              invoked immediately.
		handler    -- method to call with signature handler(self, switch)
		"""

                # Convert active/inactive to open/closed based on switch's type
		if event_type == 'active':
			if self.game.switches[name].type == 'NO':
				adjusted_event_type = 'closed'
			else:
				adjusted_event_type = 'open'
		elif event_type == 'inactive':
			if self.game.switches[name].type == 'NO':
				adjusted_event_type = 'open'
			else:
				adjusted_event_type = 'closed'
		else:
			adjusted_event_type = event_type
		et = {'closed':1, 'open':2}[adjusted_event_type]
		sw = None
		try:
			sw = self.game.switches[name]
		except KeyError:
			print("WARNING: Unknown switch %s for mode method %s in class %s!" % (name, item, self.__class__.__name__))
			return
		d = {'name':name, 'type':et, 'delay':delay, 'handler':handler, 'param':sw}
		self.__accepted_switches += [d]
	
	def status_str(self):
		return self.__class__.__name__
	
	def delay(self, name, event_type, delay, handler, param=None):
		"""Schedule the run loop to call the given handler at a later time.
		
		Keyword arguments:
		name -- string name of the event, usually the corresponding switch name
		event_type -- 'closed', 'open', or None
		delay      -- number of seconds to wait before calling the handler (float)
		handler    -- function to be called once delay seconds have elapsed
		param      -- value to be passed as the first (non-self) argument to handler.
		
		If param is None, handler's signature must be handler(self).  Otherwise,
		it is handler(self, param) to match the switch method handler pattern.
		"""
		if type(event_type) == str:
			event_type = {'closed':1, 'open':2}[event_type]
		self.__delayed += [{'name':name, 'time':time.time()+delay, 'handler':handler, 'type':event_type, 'param':param}]
		try:
			self.__delayed.sort(lambda x, y: int((x['time'] - y['time'])*100))
		except TypeError, ex:
			# Debugging code:
			for x in self.__delayed:
				print(x['name'], x['time'], type(x['time']), x['handler'], x['type'], x['param'])
			raise ex
	
	def cancel_delayed(self, name):
		"""Removes the given named delays from the delayed list, cancelling their execution."""
		if type(name) == list:
			for n in name:
				self.cancel_delayed(n)
		else:
			self.__delayed = filter(lambda x: x['name'] != name, self.__delayed)
	
	def handle_event(self, event):
		# We want to turn this event into a function call.
		sw_name = self.game.switches[event['value']].name
		handled = False

		# Filter out all of the delayed events that have been disqualified by this state change:
		self.__delayed = filter(lambda x: not (sw_name == x['name'] and x['type'] != event['type']), self.__delayed)
		
		filt = lambda x: (x['type'] == event['type']) and (x['name'] == sw_name)
		matches = filter(filt, self.__accepted_switches)
		for match in matches:
			if match['delay'] == None:
				handler = match['handler']
				result = handler(self.game.switches[match['name']])
				if result == True:
					handled = True
			else:
				self.delay(name=sw_name, event_type=match['type'], delay=match['delay'], handler=match['handler'], param=match['param'])
		return handled
		
	def mode_started(self):
		"""Notifies the mode that it is now active on the mode queue.
		
		This method should not be invoked directly; it is called by the GameController run loop.
		"""
		pass
	def mode_stopped(self):
		"""Notofies the mode that it has been removed from the mode queue.
		
		This method should not be invoked directly; it is called by the GameController run loop.
		"""
		pass
	def mode_topmost(self):
		"""Notifies the mode that it is now the topmost mode on the mode queue.
		
		This method should not be invoked directly; it is called by the GameController run loop.
		"""
		pass
	def mode_tick(self):
		"""Called by the GameController run loop during each loop when the mode is running."""
		pass
	def dispatch_delayed(self):
		"""Called by the GameController to dispatch any delayed events."""
		t = time.time()
		for item in self.__delayed:
			if item['time'] <= t:
				handler = item['handler']
				if item['param'] != None:
					handler(item['param'])
				else:
					handler()
		self.__delayed = filter(lambda x: x['time'] > t, self.__delayed)
	def __str__(self):
		return "%s  pri=%d" % (type(self).__name__, self.priority)

class ModeQueue(object):
	"""docstring for ModeQueue"""
	def __init__(self, game):
		super(ModeQueue, self).__init__()
		self.game = game
		self.modes = []
		
	def add(self, mode):
		if mode in self.modes:
			raise ValueError, "Attempted to add mode "+str(mode)+", already in mode queue."
		self.modes += [mode]
		# Sort by priority, descending:
		self.modes.sort(lambda x, y: y.priority - x.priority)
		self.game.log("Added %s, now:\n%s" % (str(mode), str(self)))
		mode.mode_started()
		if mode == self.modes[0]:
			mode.mode_topmost()

	def remove(self, mode):
		for idx, m in enumerate(self.modes):
			if m == mode:
				del self.modes[idx]
				self.game.log("Removed %s, now:\n%s" % (str(mode), str(self)))
				mode.mode_stopped()
				break
		if len(self.modes) > 0:
			self.modes[0].mode_topmost()

	def handle_event(self, event):
		modes = copy.copy(self.modes) # Make a copy so if a mode is added we don't get into a loop.
		for mode in modes:
			if mode.handle_event(event):
				return True
		return False
	
	def tick(self):
		modes = copy.copy(self.modes) # Make a copy so if a mode is added we don't get into a loop.
		for mode in modes:
			mode.dispatch_delayed()
			mode.mode_tick()
		
	def __str__(self):
		s = ""
		for mode in self.modes:
			layer = None
			if hasattr(mode, 'layer'):
				layer = mode.layer
			s += "\t\t#%d %s\t\tlayer=%s\n" % (mode.priority, type(mode).__name__, type(layer).__name__)
		return s[:-1] # Remove \n

class AttrCollection(object):
	"""docstring for AttrCollection"""
	def __init__(self):
		self.__items_by_name = {}
		self.__items_by_number = {}
	def __getattr__(self, attr):
		try:
			if type(attr) == str:
				return self.__items_by_name[attr]
			else:
				return self.__items_by_number[attr]
		except KeyError, e:
			raise KeyError, "Error looking up key %s" % (attr)
	def add(self, item, value):
		self.__items_by_name[item] = value
		self.__items_by_number[value.number] = value
	def __iter__(self):
	        for item in self.__items_by_number.itervalues():
	            yield item
	def __getitem__(self, index):
		return self.__getattr__(index)
		
class GameItem(object):
	"""Base class for Driver and Switch.  Contained in an instance of AttrCollection within the GameController."""
	def __init__(self, game, name, number):
		self.game = game
		self.name = name
		self.number = number

class Driver(GameItem):
	def __init__(self, game, name, number):
		GameItem.__init__(self, game, name, number)
		self.default_pulse_time = 30
	def disable(self):
		self.game.log("Driver %s - disable" % (self.name))
		self.game.proc.driver_disable(self.number)
	def pulse(self, milliseconds=None):
		if milliseconds == None:
			milliseconds = self.default_pulse_time
		self.game.log("Driver %s - pulse %d" % (self.name, milliseconds))
		self.game.proc.driver_pulse(self.number, milliseconds)
	def schedule(self, schedule, cycle_seconds, now):
		self.game.log("Driver %s - schedule %08x" % (self.name, schedule))
		self.game.proc.driver_schedule(number=self.number, schedule=schedule, cycle_seconds=cycle_seconds, now=now)
	def enable(self):
		self.schedule(0xffffffff, 0, True)
	def state(self):
		return self.game.proc.driver_get_state(self.number)

class Switch(GameItem):
	def __init__(self, game, name, number, type='NO'):
		GameItem.__init__(self, game, name, number)
		self.state = False
		self.last_changed = None
		self.type = type
	def set_state(self, state):
		self.state = state
		self.reset_timer()
	def is_state(self, state, seconds = None):
		if self.state == state:
			if seconds != None:
				return self.time_since_change() > seconds
			else:
				return True
		else:
			return False
	def is_active(self, seconds = None):
		if self.type == 'NO':
			return self.is_state(state=True, seconds=seconds)
		else:
			return self.is_state(state=False, seconds=seconds)
	def is_inactive(self, seconds = None):
		if self.type == 'NC':
			return self.is_state(state=True, seconds=seconds)
		else:
			return self.is_state(state=False, seconds=seconds)
	def is_open(self, seconds = None):
		return self.is_state(state=False, seconds=seconds)
	def is_closed(self, seconds = None):
		return self.is_state(state=True, seconds=seconds)
	def time_since_change(self):
		if self.last_changed == None:
			return 0.0
		else:
			return time.time() - self.last_changed
	def reset_timer(self):
		self.last_changed = time.time()
	def state_str(self):
		if self.is_closed():
			return 'closed'
		else:
			return 'open  '

class Player(object):
	"""docstring for Player"""
	def __init__(self, name):
		super(Player, self).__init__()
		self.score = 0
		self.name = name
		self.extra_balls = 0
		self.info_record = {}
	

class GameController(object):
	"""Core object comprising modes, coils, lamps, switches."""
	def __init__(self, machineType):
		super(GameController, self).__init__()
		self.machineType = machineType
		self.proc = pinproc.PinPROC(self.machineType)
		self.proc.reset(1)
		self.modes = ModeQueue(self)
		self.coils = AttrCollection()
		self.lamps = AttrCollection()
		self.switches = AttrCollection()
		self.ball = 0
		self.players = []
		self.old_players = []
		self.current_player_index = 0
		self.t0 = time.time()
		self.config = None
		self.balls_per_game = 3
		self.keyboard_events_enabled = False
	
	def __enter__(self):
		pass
	
	def __exit__(self):
		del self.proc
	
	def reset(self):
		"""Reset the game state as a slam tilt might."""
		self.ball = 0
		self.old_players = []
		self.old_players = self.players[:]
		self.players = []
		self.current_player_index = 0
		self.modes.modes = []
	
	def current_player(self):
		if len(self.players) > self.current_player_index:
			return self.players[self.current_player_index]
		else:
			return None
	
	def add_player(self, player_class=Player):
		player = player_class('Player %d' % (len(self.players) + 1))
		self.players += [player]
		return player

	def start_ball(self):
		"""Called by the implementor to notify the game that (usually the first) ball should be started."""
		self.ball_starting()

	def ball_starting(self):
		"""Called by the game framework when a new ball is starting."""
		pass
	
	def shoot_again(self):
		"""Called by the game framework when a new ball is starting which was the result of a stored extra ball (Player.extra_balls).  
		   The default implementation calls ball_starting(), which is not called by the framework in this case."""
		self.ball_starting()

	def ball_ended(self):
		"""Called by the game framework when the current ball has ended."""
		pass
	
	def end_ball(self):
		"""Called by the implementor to notify the game that the current ball has ended."""
		self.ball_ended()
		if self.current_player().extra_balls > 0:
			self.current_player().extra_balls -= 1
			self.shoot_again()
			return
		if self.current_player_index + 1 == len(self.players):
			self.ball += 1
			self.current_player_index = 0
		else:
			self.current_player_index += 1
		if self.ball > self.balls_per_game:
			self.end_game()
		else:
			self.ball_starting() # Consider: Do we want to call this here, or should it be called by the game? (for bonus sequence)
	
	def game_started(self):
		"""Called by the GameController when a new game is starting."""
		self.ball = 1
		self.players = []
		self.current_player_index = 0

	def start_game(self):
		"""Called by the implementor to notify the game that the game has started."""
		self.game_started()
	
	def game_ended(self):
		"""Called by the GameController when the current game has ended."""
		pass
		
	def end_game(self):
		"""Called by the implementor to mark notify the game that the game has ended."""
		self.game_ended()
		self.ball = 0
		
	def dmd_event(self):
		"""Called by the GameController when a DMD event has been received."""
		pass
		
	def load_config(self, filename):
		"""Reads the YAML configuration file into memory.
		Configures the switches, lamps, and coils members.
		Enables notifyHost for the open and closed debounced states on each configured switch."""
		self.config = yaml.load(open(filename, 'r'))
		pairs = [('PRCoils', self.coils, Driver), 
		         ('PRLamps', self.lamps, Driver), 
		         ('PRSwitches', self.switches, Switch)]
		for section, collection, klass in pairs:
			sect_dict = self.config[section]
			print 'Processing section: %s' % (section)
			for name in sect_dict:
				item = sect_dict[name]
				number = pinproc.decode(self.machineType, str(item['number']))
				if 'type' in item:
					collection.add(name, klass(self, name, number, type = item['type']))
				else:
					collection.add(name, klass(self, name, number))

	        sect_dict = self.config['PRBallSave']
		self.ballsearch_coils = sect_dict['pulseCoils']
		self.ballsearch_stopSwitches = sect_dict['stopSwitches']
		self.ballsearch_resetSwitches = sect_dict['resetSwitches']
                
			
		# We want to receive events for all of the defined switches:
		print "Programming switch rules: ",
		for switch in self.switches:
			print("%s," % (switch.name)),
			self.proc.switch_update_rule(switch.number, 'closed_debounced', {'notifyHost':True}, [])
			self.proc.switch_update_rule(switch.number, 'open_debounced', {'notifyHost':True}, [])
		print " ...done!"
		
		# Configure the initial switch states:
		states = self.proc.switch_get_states()
		for sw in self.switches:
				sw.set_state(states[sw.number] == 1)

		sect_dict = self.config['PRGame']
		self.num_balls_total = sect_dict['numBalls']

	def load_settings(self, template_filename, user_filename):
		"""Reads the YAML configuration file into memory.
		Configures the switches, lamps, and coils members.
		Enables notifyHost for the open and closed debounced states on each configured switch."""
		self.settings = yaml.load(open(template_filename, 'r'))
		if os.path.exists(user_filename):
			self.user_settings = yaml.load(open(user_filename, 'r'))
		else:
			self.user_settings = {}

		
		for section in self.settings:
			for item in self.settings[section]:
				if not section in self.user_settings:
					self.user_settings[section] = {}
					if 'default' in self.settings[section][item]:
						self.user_settings[section][item] = self.settings[section][item]['default']
					else:
						self.user_settings[section][item] = self.settings[section][item]['options'][0]
				elif not item in self.user_settings[section]:
					if default in self.settings[section][item]:
						self.user_settings[section][item] = self.settings[section][item]['default']
					else:
						self.user_settings[section][item] = self.settings[section][item]['options'][0]

	def write_settings(self, filename):
		"""Reads the YAML configuration file into memory.
		Configures the switches, lamps, and coils members.
		Enables notifyHost for the open and closed debounced states on each configured switch."""
		stream = file(filename, 'w')
		yaml.dump(self.user_settings, stream)

	def enable_flippers(self, enable):
		"""Enables or disables the flippers AND bumpers."""
		if self.machineType == 'wpc':
			print("Programming flippers...")
			for flipper in self.config['PRFlippers']:
				main_coil = self.coils[flipper+'Main']
				hold_coil = self.coils[flipper+'Hold']
				switch_num = self.switches[flipper].number

				drivers = []
				if enable:
					drivers += [pinproc.driver_state_pulse(main_coil.state(), 34)]
					drivers += [pinproc.driver_state_pulse(hold_coil.state(), 0)]
	
				self.proc.switch_update_rule(switch_num, 'closed_nondebounced', {'notifyHost':False}, drivers)
			
				drivers = []
				if enable:
					drivers += [pinproc.driver_state_disable(main_coil.state())]
					drivers += [pinproc.driver_state_disable(hold_coil.state())]
	
				self.proc.switch_update_rule(switch_num, 'open_nondebounced', {'notifyHost':False}, drivers)
				# Send a disable signal to make sure flipper hold is off.
				# Otherwise could be stuck on if rules disabled while hold is active.
				self.coils[flipper+'Hold'].disable()
                elif self.machineType == 'sternWhitestar' or self.machineType == 'sternSAM':
			for flipper in self.config['PRFlippers']:
				print("  programming flipper %s" % (flipper))
				main_coil = self.coils[flipper+'Main']
				#switch_num = self.switches[flipper].number
				switch_num = pinproc.decode(self.machineType, str(self.switches[flipper].number))

				drivers = []
				if enable:
					drivers += [pinproc.driver_state_patter(main_coil.state(), 3, 22, 34)]
	
				self.proc.switch_update_rule(switch_num, 'closed_nondebounced', {'notifyHost':False}, drivers)
			
				drivers = []
				if enable:
					drivers += [pinproc.driver_state_disable(main_coil.state())]
	
				self.proc.switch_update_rule(switch_num, 'open_nondebounced', {'notifyHost':False}, drivers)
				# Send a disable signal to make sure flipper is off.
				# Otherwise could be stuck on if rules disabled while flipper is pattering.
				self.coils[flipper+'Main'].disable()
	
		for bumper in self.config['PRBumpers']:
			switch_num = self.switches[bumper].number
			coil = self.coils[bumper]

			drivers = []
			if enable:
				drivers += [pinproc.driver_state_pulse(coil.state(), 20)]

			self.proc.switch_update_rule(switch_num, 'closed_nondebounced', {'notifyHost':False}, drivers)

	def install_switch_rule_coil_disable(self, switch_num, switch_state, coil_name, notify_host, enable):
		coil = self.coils[coil_name];
		drivers = []
		if enable:
			drivers += [pinproc.driver_state_disable(coil.state())]
		self.proc.switch_update_rule(switch_num, switch_state, {'notifyHost':notify_host}, drivers)

	def install_switch_rule_coil_pulse(self, switch_num, switch_state, coil_name, pulse_duration, notify_host, enable):
		coil = self.coils[coil_name];
		drivers = []
		if enable:
			drivers += [pinproc.driver_state_pulse(coil.state(),pulse_duration)]
		self.proc.switch_update_rule(switch_num, switch_state, {'notifyHost':notify_host}, drivers)

	def is_trough_full(self, num_balls=0):
		if num_balls == 0:
			num_balls = self.num_balls_total
		print "Checking for trough balls:"
		print num_balls
                if self.machineType == 'wpc':
			end_number = 6 - num_balls
			for i in range(6, end_number, -1):
				swName = 'trough' + str(i) 
				if self.switches[swName].is_closed():
					return False

			return True
					
		else:
			end_number = 1 + num_balls
			for i in range(1, end_number):
				swName = 'trough' + str(i) 
				if self.switches[swName].is_open():
					return False

			return True

	def process_event(self, event):
		event_type = event['type']
		event_value = event['value']
		if event_type == 99: # CTRL-C to quit
			print "CTRL-C detected, quiting..."	
			self.end_run_loop()
		elif event_type == 5: # DMD events
			#print "% 10.3f Frame event" % (time.time()-self.t0)
			self.dmd_event()
		else:
			sw = self.switches[event_value]
			recvd_state = event_type == 1
			if sw.state != recvd_state:
				sw.set_state(recvd_state)
				self.log("    %s:\t%s" % (sw.name, sw.state_str()))
				self.modes.handle_event(event)
			else:
				#self.log("DUPLICATE STATE RECEIVED, IGNORING: %s:\t%s" % (sw.name, sw.state_str()))
				pass

        def end_run_loop(self):
		"""Called by the programmer when he wants the run_loop to end"""
		self.done = True

	def log(self, line):
		print("% 10.3f %s" % (time.time()-self.t0, line))

	def run_loop(self):
		"""Called by the programmer to read and process switch events until interrupted."""
		loops = 0
		self.done = False
		self.dmd_event()
		try:
			while self.done == False:

				loops += 1
				if self.keyboard_events_enabled:
					# get_keyboard_events needs to be defined by
					# the keyboard handler.
					for event in self.get_keyboard_events():
						self.process_event(event)
				for event in self.proc.get_events():
					self.process_event(event)
				self.modes.tick()
				self.proc.watchdog_tickle()
		finally:
			if loops != 0:
				dt = time.time()-self.t0
				print "\nOverall loop rate: %0.3fHz\n" % (loops/dt)
