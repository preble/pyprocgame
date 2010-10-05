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

