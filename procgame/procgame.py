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
	"""docstring for Mode"""
	def __init__(self, game, priority):
		super(Mode, self).__init__()
		self.game = game
		self.priority = priority
		self.accepted_switches = []
		self.delayed = []
		self.scan_switch_handlers()
	
	def scan_switch_handlers(self):
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
			
			# Check validity of switch methods:
			try:
				self.game.switches[m.group('name')]
			except KeyError:
				print("WARNING: Unknown switch %s for mode method %s in class %s!" % (m.group('name'), item, self.__class__.__name__))
				continue

			handler = getattr(self, item)
			
			# Create a dictionary and add it:
			et = {'closed':1, 'open':2}[m.group('state')]
			d = {'name':m.group('name'), 'type':et, 'delay':seconds, 'handler':handler}
			#print("accepted_switches += %s" % (str(d)))
			self.accepted_switches += [d]
			
	def status_str(self):
		return self.__class__.__name__
	
	def delay(self, name, event_type, delay, handler):
		self.delayed += [{'name':name, 'time':time.time()+delay, 'handler':handler, 'type':event_type}]
		self.delayed.sort(lambda x, y: x['time'] - y['time'])
	
	def handle_event(self, event):
		# We want to turn this event into a function call.
		sw_name = self.game.switches[event['value']].name
		handled = False

		# Filter out all of the delayed events that have been disqualified by this state change:
		self.delayed = filter(lambda x: not (sw_name == x['name'] and x['type'] != event['type']), self.delayed)
		
		filt = lambda x: (x['type'] == event['type']) and (x['name'] == sw_name)
		matches = filter(filt, self.accepted_switches)
		for match in matches:
			if match['delay'] == None:
				result = match['handler']()
				if result == True:
					handled = True
			else:
				self.delay(name=sw_name, event_type=match['type'], delay=match['delay'], handler=match['handler'])
		return handled
		
	def mode_started(self):
		pass
	def mode_stopped(self):
		pass
	def mode_topmost(self):
		pass
	def mode_tick(self):
		# Dispatch any qualifying delayed events:
		t = time.time()
		for item in self.delayed:
			if item['time'] > t:
				break
			handler = item['handler']
			handler()
		self.delayed = filter(lambda x: x['time'] > t, self.delayed)

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
		self.items_by_name = {}
		self.items_by_number = {}
	def __getattr__(self, attr):
		if type(attr) == str:
			return self.items_by_name[attr]
		else:
			return self.items_by_number[attr]
	def add(self, item, value):
		self.items_by_name[item] = value
		self.items_by_number[value.number] = value
	def __iter__(self):
	        for item in self.items_by_number.itervalues():
	            yield item
	def __getitem__(self, index):
		return self.__getattr__(index)
		
class GameItem(object):
	def __init__(self, game, name, number):
		self.game = game
		self.name = name
		self.number = number

class Driver(GameItem):
	def disable(self):
		print("Driver %s - disable" % (self.name))
		self.game.proc.driver_disable(self.number)
	def pulse(self, milliseconds):
		print("Driver %s - pulse %d" % (self.name, milliseconds))
		self.game.proc.driver_pulse(self.number, milliseconds)
	def schedule(self, schedule, cycle_seconds, now):
		print("Driver %s - schedule %08x" % (self.name, schedule))
		self.game.proc.driver_schedule(number=self.number, schedule=schedule, cycle_seconds=cycle_seconds, now=now)
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
	"""docstring for GameController"""
	def __init__(self, machineType):
		super(GameController, self).__init__()
		self.machineType = machineType
		self.proc = pinproc.PinPROC(self.machineType)
		self.modes = ModeQueue()
		self.coils = AttrCollection()
		self.lamps = AttrCollection()
		self.switches = AttrCollection()
		self.t0 = time.time()
	
	def __enter__(self):
		pass
	
	def __exit__(self):
		del self.proc
		
	def load_config(self, filename):
		yaml_dict = yaml.load(open(filename, 'r'))
		pairs = [('PRCoils', self.coils, Driver), 
		         ('PRLamps', self.lamps, Driver), 
		         ('PRSwitches', self.switches, Switch)]
		for section, collection, klass in pairs:
			sect_dict = yaml_dict[section]
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
		
		for flipper in yaml_dict['PRFlippers']:
			print("  programming flipper %s" % (flipper))
			main_coil = self.coils[flipper+'Main']
			hold_coil = self.coils[flipper+'Hold']
			switch_num = self.switches[flipper].number
			
			main_state = pinproc.driver_state_pulse(main_coil.state(), 34)
			hold_state = pinproc.driver_state_pulse(hold_coil.state(), 0)
			
			self.proc.switch_update_rule(switch_num, 'closed_nondebounced', {'notifyHost':False}, [main_state, hold_state])
			#self.proc.switch_update_rule(switch_num, 'closed_debounced', {'notifyHost':True}, [])
			
			main_state = pinproc.driver_state_disable(main_coil.state())
			hold_state = pinproc.driver_state_disable(hold_coil.state())
			
			self.proc.switch_update_rule(switch_num, 'open_nondebounced', {'notifyHost':False}, [main_state, hold_state])
			#self.proc.switch_update_rule(switch_num, 'open_debounced', {'notifyHost':True}, [])
		
		for bumper in yaml_dict['PRBumpers']:
			switch_num = self.switches[bumper].number
			coil = self.coils[bumper]
			state = pinproc.driver_state_pulse(coil.state(), 34)
			self.proc.switch_update_rule(switch_num, 'closed_nondebounced', {'notifyHost':False}, [state])
			#self.proc.switch_update_rule(switch_num, 'closed_debounced', {'notifyHost':True}, [])
		
		states = self.proc.switch_get_states()
		for sw_num in range(len(states)):
			if sw_num in self.switches.items_by_number:
				self.switches.items_by_number[sw_num].set_state(states[sw_num] == 1)
	
	def run_loop(self):
		"""docstring for run_loop"""
		#try:
		while True:
			for event in self.proc.get_events():
				event_type = event['type']
				event_value = event['value']
				sw = self.switches.items_by_number[event_value]
				sw.set_state(event_type == 1)
				print "% 10.3f %s:\t%s" % (time.time()-self.t0, sw.name, sw.state_str())
				self.modes.handle_event(event)
			self.modes.tick()
			self.proc.watchdog_tickle()
		#except Exception, e:
		#	raise e


# def main(machineType):
# 	"""main"""
# 	with GameController(machineType) as proc:
# 		proc.modes.add(AttractMode())
# 		proc.run_loop()
# 
# if __name__ == '__main__': main('wpc')
