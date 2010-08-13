import time

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
	"""Base class for :class:`Driver` and :class:`Switch`.  Contained in an instance of :class:`AttrCollection` within the :class:`GameController`."""
	game = None
	""":class:`GameController` to which this item belongs."""
	name = None
	"""String name of this item."""
	number = None
	"""Integer value for this item providing a mapping to the hardware."""
	def __init__(self, game, name, number):
		self.game = game
		self.name = name
		self.number = number

class Driver(GameItem):
	"""Represents a driver in a pinball machine, such as a lamp, coil/solenoid, or flasher.
	
	Subclass of :class:`GameItem`.
	"""
	
	default_pulse_time = 30
	"""Default number of milliseconds to pulse this driver.  See :meth:`pulse`."""
	last_time_changed = 0
	"""The last :class:`time` that this driver's state was modified."""
	
	def __init__(self, game, name, number):
		GameItem.__init__(self, game, name, number)
	def disable(self):
		"""Disables (turns off) this driver."""
		self.game.log("Driver %s - disable" % (self.name))
		self.game.proc.driver_disable(self.number)
		self.last_time_changed = time.time()
	def pulse(self, milliseconds=None):
		"""Enables this driver for `milliseconds`.
		
		If no parameters are provided or `milliseconds` is `None`, :attr:`default_pulse_time` is used."""
		if milliseconds == None:
			milliseconds = self.default_pulse_time
		self.game.log("Driver %s - pulse %d" % (self.name, milliseconds))
		self.game.proc.driver_pulse(self.number, milliseconds)
		self.last_time_changed = time.time()
	def schedule(self, schedule, cycle_seconds, now):
		"""Schedules this driver to be enabled according to the given `schedule` bitmask."""
		self.game.log("Driver %s - schedule %08x" % (self.name, schedule))
		self.game.proc.driver_schedule(number=self.number, schedule=schedule, cycle_seconds=cycle_seconds, now=now)
		self.last_time_changed = time.time()
	def enable(self):
		"""Enables this driver indefinitely.
		
		.. warning::
		
			Never use this method with high voltage drivers such as coils and flashers!
			Instead, use time-limited methods such as :meth:`pulse` and :meth:`schedule`.
		
		"""
		self.schedule(0xffffffff, 0, True)
		self.last_time_changed = time.time()
	def state(self):
		"""Returns a dictionary representing this driver's current configuration state."""
		return self.game.proc.driver_get_state(self.number)

class Switch(GameItem):
	"""Represents a switch in a pinball machine.
	
	Switches are accessed using :attr:`GameController.switches`.
	
	Subclass of :class:`GameItem`.
	"""
	
	state = False
	"""`False` indicates open, `True` is closed.
	In most applications the :meth:`is_active` and :meth:`is_inactive` methods should be used to determine a switch's state."""
	last_changed = None
	""":class:`time` of the last state change of this switch.  `None` if the :class:`GameController` has not yet initialized this switch's state."""
	type = None
	"""``'NO'`` (normally open) or ``'NC'`` (normally closed).  Mechanical switches are usually NO, while opto switches are almost always NC.  
	This is used to determine whether a switch is active ("in contact with the ball") without ruleset code needing to be concerned with the details of the switch hardware."""
	
	def __init__(self, game, name, number, type='NO'):
		GameItem.__init__(self, game, name, number)
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
		"""`True` if the ball is activating this switch, or if this switch is somehow being activated.
		If `seconds` is not `None` (the default), only returns `True` if the switch has been active for that number of seconds."""
		if self.type == 'NO':
			return self.is_state(state=True, seconds=seconds)
		else:
			return self.is_state(state=False, seconds=seconds)
	def is_inactive(self, seconds = None):
		"""`True` if the ball is not activating this switch
		If `seconds` is not `None` (the default), only returns `True` if the switch has not been active for that number of seconds."""
		if self.type == 'NC':
			return self.is_state(state=True, seconds=seconds)
		else:
			return self.is_state(state=False, seconds=seconds)
	def is_open(self, seconds = None):
		return self.is_state(state=False, seconds=seconds)
	def is_closed(self, seconds = None):
		return self.is_state(state=True, seconds=seconds)
	def time_since_change(self):
		"""Number of seconds that this switch has been in its current state.
		This value is reset to 0 by the :class:`GameController` *after* the switch event has been processed by the active :class:`Mode` instances."""
		if self.last_changed == None:
			return 0.0
		else:
			return time.time() - self.last_changed
	def reset_timer(self):
		"""Resets the value returned by :meth:`time_since_change` to 0.0.  Normally this is called by the :class:`GameController`, but it can be triggered manually if needed."""
		self.last_changed = time.time()
	def state_str(self):
		if self.is_closed():
			return 'closed'
		else:
			return 'open  '


class Player(object):
	"""Represents a player in the game.
	The game maintains a collection of players in :attr:`GameController.players`."""
	
	score = 0
	"""This player's score."""
	
	name = None
	"""This player's name."""

	extra_balls = 0
	"""Number of extra balls that this player has earned."""
	
	game_time = 0
	"""Number of seconds that this player has had the ball in play."""
	
	def __init__(self, name):
		super(Player, self).__init__()
		self.name = name

