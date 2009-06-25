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
		handler_func_re = re.compile('sw_(?P<name>[a-zA-Z0-9]+)_(?P<state>open|closed)(?P<after>_for_(?P<time>[0-9]+)(?P<units>ms|s))?')
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
		event_type -- 'open' or 'closed'
		delay      -- float number of seconds that the state should be held 
		              before invoking the handler, or None if it should be
		              invoked immediately.
		handler    -- method to call with signature handler(self, switch)
		"""
		et = {'closed':1, 'open':2}[event_type]
		sw = None
		try:
			sw = self.game.switches[name]
		except KeyError:
			print("WARNING: Unknown switch %s for mode method %s in class %s!" % (m.group('name'), item, self.__class__.__name__))
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
		self.__delayed.sort(lambda x, y: x['time'] - y['time'])
	
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
		# Dispatch any qualifying delayed events:
		t = time.time()
		for item in self.__delayed:
			if item['time'] > t:
				break
			handler = item['handler']
			if item['param'] != None:
				handler(item['param'])
			else:
				handler()
		self.__delayed = filter(lambda x: x['time'] > t, self.__delayed)

class ModeQueue(object):
	"""docstring for ModeQueue"""
	def __init__(self):
		super(ModeQueue, self).__init__()
		self.modes = []
		
	def add(self, mode):
		self.modes += [mode]
		# Sort by priority, descending:
		self.modes.sort(lambda x, y: y.priority - x.priority)
		mode.mode_started()
		if mode == self.modes[0]:
			mode.mode_topmost()

	def remove(self, mode):
		mode.mode_stopped()
		for idx, m in enumerate(self.modes):
			if m == mode:
				del self.modes[idx]
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
			mode.mode_tick()
		

class AttrCollection(object):
	"""docstring for AttrCollection"""
	def __init__(self):
		self.__items_by_name = {}
		self.__items_by_number = {}
	def __getattr__(self, attr):
		if type(attr) == str:
			return self.__items_by_name[attr]
		else:
			return self.__items_by_number[attr]
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
		print("Driver %s - disable" % (self.name))
		self.game.proc.driver_disable(self.number)
	def pulse(self, milliseconds=None):
		if milliseconds == None:
			milliseconds = self.default_pulse_time
		print("Driver %s - pulse %d" % (self.name, milliseconds))
		self.game.proc.driver_pulse(self.number, milliseconds)
	def schedule(self, schedule, cycle_seconds, now):
		print("Driver %s - schedule %08x" % (self.name, schedule))
		self.game.proc.driver_schedule(number=self.number, schedule=schedule, cycle_seconds=cycle_seconds, now=now)
	def enable(self):
		self.schedule(0xffffffff, 0, True)
	def state(self):
		return self.game.proc.driver_get_state(self.number)

class Switch(GameItem):
	def __init__(self, game, name, number):
		GameItem.__init__(self, game, name, number)
		self.state = False
		self.last_changed = None
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



class GameController(object):
	"""Core object comprising modes, coils, lamps, switches."""
	def __init__(self, machineType):
		super(GameController, self).__init__()
		self.machineType = machineType
		self.proc = pinproc.PinPROC(self.machineType)
		self.modes = ModeQueue()
		self.coils = AttrCollection()
		self.lamps = AttrCollection()
		self.switches = AttrCollection()
		self.t0 = time.time()
		self.config = None
	
	def __enter__(self):
		pass
	
	def __exit__(self):
		del self.proc
		
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
				collection.add(name, klass(self, name, number))
		
		# We want to receive events for all of the defined switches:
		for switch in self.switches:
			print("  programming rule for %s" % (switch.name))
			self.proc.switch_update_rule(switch.number, 'closed_debounced', {'notifyHost':True}, [])
			self.proc.switch_update_rule(switch.number, 'open_debounced', {'notifyHost':True}, [])
		
		# Configure the initial switch states:
		states = self.proc.switch_get_states()
		for sw in self.switches:
				sw.set_state(states[sw.number] == 1)
	
	def enable_flippers(self, enable):
		"""Enables or disables the flippers AND bumpers."""
		for flipper in self.config['PRFlippers']:
			print("  programming flipper %s" % (flipper))
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
	
		for bumper in self.config['PRBumpers']:
			switch_num = self.switches[bumper].number
			coil = self.coils[bumper]

			drivers = []
			if enable:
				drivers += [pinproc.driver_state_pulse(coil.state(), 34)]

			self.proc.switch_update_rule(switch_num, 'closed_nondebounced', {'notifyHost':False}, drivers)

	def run_loop(self):
		"""Called by the programmer to read and process switch events until interrupted."""
		while True:
			for event in self.proc.get_events():
				event_type = event['type']
				event_value = event['value']
				sw = self.switches[event_value]
				sw.set_state(event_type == 1)
				print "% 10.3f %s:\t%s" % (time.time()-self.t0, sw.name, sw.state_str())
				self.modes.handle_event(event)
			self.modes.tick()
			self.proc.watchdog_tickle()
