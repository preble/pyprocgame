from game import *

class BasicDropTargetBank(Mode):
	"""Basic Drop Target Bank mode."""
	def __init__(self, game, priority, prefix, letters):
		Mode.__init__(self, game, 8)
		self.letters = letters
		self.prefix = prefix
		# Ordinarily a mode would have sw_switchName_open() handlers, 
		# but because this is a generic Mode we will configure them
		# programatically to all call the dropped() method:
		for letter in self.letters:
			self.add_switch_handler(name=self.prefix+letter, event_type='open', delay=None, handler=self.dropped)

	def mode_started(self):
		self.chase_lamps()
		self.schedule_delayed_reset(delay=1.0)
		
	def dropped(self, sw):
		"""'global' handler for drop target drops"""
		self.game.lamps[sw.name].schedule(schedule=0xf0f0f0f0, cycle_seconds=1, now=True)
		for letter in self.letters:
			if self.game.switches[self.prefix+letter].is_closed():
				return
		# If we're here, then all of the targets in the bank are down!
		self.chase_lamps()
		self.schedule_delayed_reset()
	
	def chase_lamps(self):
		bits = 3
		schedule = ~(0xffffffff << bits)
		for letter in self.letters:
			self.game.lamps[self.prefix+letter].schedule(schedule=(schedule|(schedule << 16)), cycle_seconds=4, now=True)
			schedule <<= bits
	
	def schedule_delayed_reset(self, delay=2.0):
		self.delay(name='reset', event_type=None, delay=delay, handler=self.reset_drop_target_bank)
	
	def reset_drop_target_bank(self):
		self.game.coils.resetDropTarget.pulse()
		for letter in self.letters:
			self.game.lamps[self.prefix+letter].enable()
