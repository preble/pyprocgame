from game import *

class BasicDropTargetBank(Mode):
	"""Basic Drop Target Bank mode."""
	def __init__(self, game, priority, prefix, letters):
		Mode.__init__(self, game, 8)
		self.letters = letters
		self.prefix = prefix
		self.on_completed = None
		self.on_advance = None
		# Ordinarily a mode would have sw_switchName_open() handlers, 
		# but because this is a generic Mode we will configure them
		# programatically to all call the dropped() method:
		for name in self.names():
			self.add_switch_handler(name=name, event_type='open', delay=None, handler=self.dropped)

	def mode_started(self):
		self.animated_reset(seconds=1.0)
		
	def dropped(self, sw):
		"""General handler for all drop target switches"""
		self.game.lamps[sw.name].schedule(schedule=0xf0f0f0f0, cycle_seconds=1, now=True)
		if self.all_down():
			self.on_completed(self)
			self.animated_reset(seconds=2.0)
		else:
			self.on_advance(self)
	
	def chase_lamps(self):
		"""Perform an animation using the lamps."""
		bits = 3
		schedule = ~(0xffffffff << bits)
		for name in self.names():
			self.game.lamps[name].schedule(schedule=(schedule|(schedule << 16)), cycle_seconds=4, now=True)
			schedule <<= bits
	
	def animated_reset(self, seconds):
		"""Perform an animation using the lamps and then reset the drop targets."""
		self.chase_lamps()
		self.schedule_delayed_reset(seconds)
	
	def schedule_delayed_reset(self, delay):
		"""Schedule a call to reset_drop_target_bank() for 'delay' seconds in the future."""
		self.delay(name='reset', event_type=None, delay=delay, handler=self.reset_drop_target_bank)
	
	def reset_drop_target_bank(self):
		"""Resets the drop targets to the up position and lights each of the lamps."""
		self.game.coils.resetDropTarget.pulse()
		for name in self.names():
			self.game.lamps[name].enable()
	
	def all_down(self):
		"""Returns True if all of the drop targets are down."""
		for name in self.names():
			if self.game.switches[name].is_closed():
				return False
		return True
	
	def names(self):
		"""Returns the drop target switch/lamp names in order."""
		for letter in self.letters:
			yield self.prefix+letter

class ProgressiveDropTargetBank(BasicDropTargetBank):
	"""Implements a drop target bank that requires that the targets be hit in order.
	The advance_switch argument should be the name of the switch that, when closed, causes the current target to advance."""
	def __init__(self, game, priority, prefix, letters, advance_switch):
		super(ProgressiveDropTargetBank, self).__init__(game, priority, prefix, letters)
		self.add_switch_handler(name=advance_switch, event_type='closed', delay=None, handler=self.__advance_triggered)
		self.advance_switch = self.game.switches[advance_switch]
		self.current_target = None # Set by animated_reset() on mode start.
	
	def advance(self):
		"""Advances the current target to the next target.
		If the last target is active, the bank will perform an animated reset.
		If all of the targets are down the bank will be physically reset but the current target will be advanced normally."""
		use_next = False
		new_target = None
		for letter in self.letters:
			name = self.prefix + letter
			if use_next:
				new_target = name
				break
			if self.current_target == name:
				use_next = True
		if new_target == None:
			# All of them must be down!
			self.on_completed(self)
			self.animated_reset(2.0)
		else:
			self.on_advance(self)
			self.game.lamps[self.current_target].enable()
			self.current_target = new_target
			self.game.lamps[self.current_target].schedule(schedule=0xf0f0f0f0, cycle_seconds=0, now=True)
			if self.all_down():
				self.reset_drop_target_bank()
			
	def dropped(self, sw):
		"""General handler for all individual drop target switch events.
		Advances the current target if it was hit.  
		Otherwise it advances and physically resets the bank if all targets are now down."""
		if sw.name == self.current_target:
			self.advance()
		elif self.all_down():
			self.advance()
			self.reset_drop_target_bank()

	def animated_reset(self, seconds):
		"""Performs an animated reset and sets the current target back to the first target."""
		self.current_target = self.prefix + self.letters[0]
		super(ProgressiveDropTargetBank, self).animated_reset(seconds)

	def reset_drop_target_bank(self):
		"""Resets the drop targets to the up position and configures the lamps to reflect the current target state."""
		self.game.coils.resetDropTarget.pulse()
		before = True
		for name in self.names():
			if name == self.current_target:
				self.game.lamps[name].schedule(schedule=0xf0f0f0f0, cycle_seconds=0, now=True)
				before = False
			elif before:
				self.game.lamps[name].enable()
			else:
				self.game.lamps[name].disable()
	
	def __advance_triggered(self, sw):
		"""Switch event handler for the advance_switch configured on mode creation."""
		self.advance()
