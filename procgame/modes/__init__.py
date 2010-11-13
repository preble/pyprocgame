__all__ = [
	'ballsave',
	'ballsearch',
	'drops'
	'replay',
	'scoredisplay',
	'trough',
	]
from ballsave import *
from ballsearch import *
from drops import *
from replay import *
from scoredisplay import *
from trough import *

from ..game import Mode
class TransitionOutHelperMode(Mode):
	def __init__(self, game, priority, transition, layer):
		super(TransitionOutHelperMode, self).__init__(game=game, priority=priority)
		self.layer = layer
		self.layer.transition = transition
		self.layer.transition.in_out = 'out'
		self.layer.transition.completed_handler = self.transition_completed
	def mode_started(self):
		self.layer.transition.start()
	def transition_completed(self):
		self.game.modes.remove(self)


class SwitchSequenceRecognizer(Mode):
	"""Listens to switch events to detect and act upon sequences."""
	
	switches = {}
	
	switch_log = []
	
	def __init__(self, game, priority):
		super(SwitchSequenceRecognizer, self).__init__(game=game, priority=priority)
		self.switches = {}
		self.switch_log = []
	
	def add_sequence(self, sequence, handler):
		unique_switch_names = list(set(map(lambda sw: sw.name, sequence)))
		sequence_switch_nums = map(lambda sw: sw.number, sequence)
		#sequence_str = self.switch_separator_char.join(sequence_switch_nums)
		self.switches[tuple(sequence_switch_nums)] = handler
		for sw in unique_switch_names:
			# No concern about duplicate switch handlers, as add_switch_handler() protects against this.
			self.add_switch_handler(name=sw, event_type='active', delay=None, handler=self.switch_active)
	
	def reset(self):
		"""Resets the remembered sequence."""
		self.switch_log = []
	
	def switch_active(self, sw):
		self.switch_log.append(sw.number)
		log_tuple = tuple(self.switch_log)
		for sequence, handler in self.switches.items():
			if log_tuple[-len(sequence):] == sequence:
				handler()
