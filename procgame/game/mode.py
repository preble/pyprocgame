import time
import re
import copy
import logging
import uuid

# Documented in game.rst:
SwitchStop = True
SwitchContinue = False

class Mode(object):
	"""Abstraction of a game mode to be subclassed by the game
	programmer.
	
	Modes are essentially a collection of switch even thandlers.
	Active modes are held in :attr:`GameController.modes`, an
	instance of :class:`ModeQueue`,
	which dispatches event notifications to modes in
	order of priority (highest to lowest).  If a higher priority
	mode's switch event handler method returns
	:data:`~procgame.game.SwitchStop`, the event
	is not passed down to lower modes.
	
	Switch event handlers are detected when the :class:`Mode`
	initializer is called by the subclass.
	Various switch event handler formats are recognized:
	
	``sw_switchName_open(self, sw)``
	  Called when a switch (named switchName) is opened.
	``sw_switchName_closed(self, sw)``
	  Closed variant of the above.
	``sw_switchName_open_for_1s(self, sw)``
	  Called when switchName has been open continuously for one second
	
	Example variants of the above: ::
	
		def sw_switchName_closed_for_2s(self, sw):
			pass
		
		def sw_switchName_closed_for_100ms(self, sw):
			pass
		
		def sw_switchName_open_for_500ms(self, sw):
			pass
	
	.. NOTE::
		Presently only switch names with the characters a-z, A-Z, and 0-9 are recognized.
		If a switch name has an underscore in it, the switch handler will not be recognized.
	
	Modes can be programatically configured using :meth:`.add_switch_handler`.
	"""
	
	parent_mode = None
	"""The parent mode for this mode.  Set by :meth:`add_child_mode` and cleared in :meth:`remove_child_mode`."""
	__children = None # child modes, managed with add_child_mode() and remove_child_mode()
	
	def __init__(self, game, priority):
		super(Mode, self).__init__()
		self.game = game
		self.priority = priority
		self.__accepted_switches = []
		self.__delayed = []
		self.__children = []
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
			
			switch_name = m.group('name')
			switch_state = m.group('state')
			
			if switch_name not in self.game.switches:
				raise ValueError, 'Unrecognized switch name %s in handler %s.%s().' % (switch_name, self.__class__.__name__, item)

			self.add_switch_handler(name=switch_name, event_type=switch_state, delay=seconds, handler=handler)
	
	def add_switch_handler(self, name, event_type, delay, handler):
		"""Programatically configure a switch event handler.
		
		Keyword arguments:
		
		``name``
		  valid switch name
		``event_type``
		  'open','closed','active', or 'inactive'
		``delay``
		  float number of seconds that the state should be held 
		  before invoking the handler, or None if it should be
		  invoked immediately.
		``handler``
		  method to call with signature ``handler(self, switch)``
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
		if self.game.switches[name].debounce:
			et = {'closed':1, 'open':2}[adjusted_event_type]
		else:
			et = {'closed':3, 'open':4}[adjusted_event_type]
		sw = None
		try:
			sw = self.game.switches[name]
		except KeyError:
			self.game.logger.error("WARNING: add_switch_handler(): Switch %s unknown. Please check your machine configuration file." % (name))
			return
		d = {'name':name, 'type':et, 'delay':delay, 'handler':handler, 'param':sw}
		if d not in self.__accepted_switches:
			self.__accepted_switches.append(Mode.AcceptedSwitch(name=name, event_type=et, delay=delay, handler=handler, param=sw))
	
	def status_str(self):
		return self.__class__.__name__
	
	def delay(self, name=None, event_type=None, delay=0, handler=None, param=None):
		"""Schedule the run loop to call the given handler at a later time.
		
		Keyword arguments:
		
		``name``
			Switch name for this event.  If using this method for a delayed
			method call, use ``None`` and a name will be generated for you.
			The generated name can be obtained from the return value.
		``event_type``
			'closed', 'open', or ``None``.
		``delay``
			Number of seconds to wait before calling the handler (float).
		``handler``
			Function to be called once delay seconds have elapsed.
		``param``
			Value to be passed as the first (non-self) argument to handler.
		
		If param is None, handler's signature must be ``handler(self)``.  Otherwise,
		it is ``handler(self, param)`` to match the switch method handler pattern.
		
		Returns the ``name`` of the delay, which may later be used with :meth:`cancel_delayed`.
		
		Example usage for delayed method invocation::
		
			def delayed_handler(self):
				print 'thatButton was pressed 2 seconds ago!'
			
			def sw_thatButton_active(self):
				# After 2 seconds, call delayed_handler() above.
				self.delayed_name = self.delay(delay=2.0, handler=self.delayed_handler)
				# Store name to cancel the delay later: self.cancel_delayed(self.delayed_name)
		
		"""
		if type(event_type) == str:
			event_type = {'closed':1, 'open':2}[event_type]
		if name == None:
			name = 'anon_delay'+str(uuid.uuid1())
		self.__delayed.append(Mode.Delayed(name=name, time=time.time()+delay, handler=handler, event_type=event_type, param=param))
		try:
			self.__delayed.sort(lambda x, y: int((x.time - y.time)*100))
		except TypeError, ex:
			# Debugging code:
			for x in self.__delayed:
				print(x)
			raise ex
		return name
	
	def cancel_delayed(self, name):
		"""Removes the given named delays from the delayed list, cancelling their execution."""
		if type(name) == list:
			for n in name:
				self.cancel_delayed(n)
		else:
			self.__delayed = filter(lambda x: x.name != name, self.__delayed)
	
	def handle_event(self, event):
		# We want to turn this event into a function call.
		sw_name = self.game.switches[event['value']].name
		handled = False

		# Filter out all of the delayed events that have been disqualified by this state change.
		# Remove all items that are for this switch (sw_name) but for a different state (type).
		# Put another way, keep delayed items pertaining to other switches, plus delayed items 
		# pertaining to this switch for another state.
		self.__delayed = filter(lambda x: not (sw_name == x.name and x.event_type != event['type']), self.__delayed)
		
		filt = lambda accepted: (accepted.event_type == event['type']) and (accepted.name == sw_name)
		for accepted in filter(filt, self.__accepted_switches):
			if accepted.delay == None or accepted.delay == 0:
				handler = accepted.handler
				result = handler(self.game.switches[accepted.name])
				if result == SwitchStop:
					handled = True
			else:
				self.delay(name=sw_name, event_type=accepted.event_type, delay=accepted.delay, handler=accepted.handler, param=accepted.param)
		return handled
		
	def mode_started(self):
		"""Notifies the mode that it is now active on the mode queue.
		
		This method should not be invoked directly; it is called by the GameController run loop.
		"""
		for child in self.__children:
			self.game.modes.add(child)
		
	def mode_stopped(self):
		"""Notifies the mode that it has been removed from the mode queue.
		
		This method should not be invoked directly; it is called by the GameController run loop.
		"""
		for child in self.__children:
			self.game.modes.remove(child)
		
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
			if item.time <= t:
				handler = item.handler
				if item.param != None:
					handler(item.param)
				else:
					handler()
		self.__delayed = filter(lambda x: x.time > t, self.__delayed)

	def is_started(self):
		"""Returns ``True`` if this mode is on the mode queue (:meth:`mode_started` has already been called)."""
		return self in self.game.modes

	def add_child_mode(self, mode):
		"""Add *mode* as a child of the receiver.
		Child modes are added and removed from the game's mode queue when
		:meth:`mode_started` and :meth:`mode_stopped` are called, respectively.
		
		If this mode is already on the mode queue (:meth:`is_started` == ``True``),
		then *mode* will be added (started) immediately.
		
		Sets *mode*'s :attr:`parent_mode` to the receiver.
		
		:return: *mode*"""
		if mode in self.__children:
			return mode
		self.__children.append(mode)
		mode.parent_mode = self
		if self.is_started():
			self.game.modes.add(mode)
		return mode
	
	def remove_child_mode(self, mode):
		"""Remove *mode* as a child of the receiver.
		See :meth:`add_child_mode` for a description of child modes.
		If this mode is already on the mode queue,
		the *mode* will be removed (stopped) immediately.
		
		Sets *mode*'s :attr:`parent_mode` to ``None``.
		
		See also: :meth:`add_child_mode`."""
		if mode in self.__children:
			self.__children.remove(mode)
			mode.parent_mode = None
			if self.is_started():
				self.game.modes.remove(mode)
		return mode
	
	def __str__(self):
		return "%s  pri=%d" % (type(self).__name__, self.priority)
	def update_lamps(self):
		"""Called by the GameController re-apply active lamp schedules"""
		pass
	
	# Data structure used by the __accepted_switches array:
	class AcceptedSwitch:
		def __init__(self, name, event_type, delay, handler, param):
			self.name = name
			self.event_type = event_type
			self.delay = delay
			self.handler = handler
			self.param = param
		def __str__(self):
			return '<name=%s event_type=%s delay=%s>' % (self.name, self.event_type, self.delay)
	
	# Data structure used by the __delayed array:
	class Delayed:
		def __init__(self, name, time, handler, event_type, param):
			self.name = name
			self.time = time
			self.handler = handler
			self.event_type = event_type
			self.param = param
		def __str__(self):
			return '<name=%s time=%s event_type=%s>' % (self.name, self.time, self.event_type)

class ModeQueue(object):
	"""A queue of modes which dispatches switch events."""
	
	changed = False
	"""True if the contents of the queue has changed since the last time this variable was set to False."""
	
	def __init__(self, game):
		super(ModeQueue, self).__init__()
		self.game = game
		self.modes = []
		self.logger = logging.getLogger('game.modes')
		
	def add(self, mode):
		if mode in self.modes:
			raise ValueError, "Attempted to add mode "+str(mode)+", already in mode queue."
		self.modes += [mode]
		# Sort by priority, descending:
		self.modes.sort(lambda x, y: y.priority - x.priority)
		self.changed = True
		self.logger.info("Added %s.", str(mode))
		mode.mode_started()
		if mode == self.modes[0]:
			mode.mode_topmost()

	def remove(self, mode):
		for idx, m in enumerate(self.modes):
			if m == mode:
				del self.modes[idx]
				self.changed = True
				self.logger.info("Removed %s.", str(mode))
				mode.mode_stopped()
				break
		if len(self.modes) > 0:
			self.modes[0].mode_topmost()
	
	def __iter__(self):
		return self.modes.__iter__()
	
	def __len__(self):
		return len(self.modes)
	
	def __contains__(self, mode):
		return mode in self.modes
	
	def __getitem__(self, v):
		return self.modes[v]
	
	def handle_event(self, event):
		modes = copy.copy(self.modes) # Make a copy so if a mode is added we don't get into a loop.
		for mode in modes:
			handled = mode.handle_event(event)
			if handled:
				break
	
	def tick(self):
		modes = copy.copy(self.modes) # Make a copy so if a mode is added we don't get into a loop.
		for mode in modes:
			mode.dispatch_delayed()
			mode.mode_tick()
	
	def log_queue(self, log_level=logging.INFO):
		log_rows = []
		
		for mode in self.modes:
			layer = None
			if hasattr(mode, 'layer'):
				layer = mode.layer
			if layer:
				log_rows.append([str(mode.priority), type(mode).__name__, type(layer).__name__])
			else:
				log_rows.append([str(mode.priority), type(mode).__name__, '-'])
		
		for line in tabularize(log_rows):
			self.logger.log(log_level, '  '+line)

def tabularize(rows, col_spacing=2):
	"""*rows* should be a list of lists of strings: [[r1c1, r1c2], [r2c1, r2c2], ..].
	Returns a list of formatted lines of text, with column values left justified."""
	
	# Find the column widths:
	max_column_widths = []
	for row in rows:
		while len(row) > len(max_column_widths):
			max_column_widths.append(0)
		for index, col in enumerate(row):
			if len(col) > max_column_widths[index]:
				max_column_widths[index] = len(col)
	# Now that we have the column widths, create the individual lines:
	output = []
	for row in rows:
		line = ''
		for index, col in enumerate(row):
			line += col.ljust(max_column_widths[index]+col_spacing)
		output.append(line)
	return output
