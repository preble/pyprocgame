from entry import *
from .. import game

import time


class EntryPrompt:
	"""Used by :class:`HighScoreLogic` subclasses' :meth:`HighScoreLogic.prompts` methods
	to communicate which scores need to be prompted for.
	"""
	
	key = None
	"""Object that will be used to identify this prompt when :meth:`HighScoreLogic.store_initials` is called."""
	
	left = None
	"""String or array of strings to be displayed on the left side of :class:`InitialEntryMode`."""
	
	right = None
	"""String or array of strings to be displayed on the right side of :class:`InitialEntryMode`."""
	
	def __init__(self, key=None, left=None, right=None):
		self.key = key
		self.left = left
		self.right = right


class HighScoreLogic:
	"""Interface used by :class:`EntrySequenceManager` to abstract away the details of high score entry and storage."""

	def prompts(self):
		"""Return a list of :class:`EntryPrompt` objects to be presented to the player, in order.
		"""
		return list()
	def store_initials(self, key, inits):
		"""Called by :class:`EntrySequenceManager` to store the entered initials."""
		pass

class HighScore:
	"""Model class.
	
	:attr:`score`, :attr:`inits` and :attr:`date` are persisted via the dictionary with
	:meth:`from_dict` and :meth:`to_dict`.  The remaining attributes are used to maintain state.
	"""

	score = 0
	"""Numeric high score value."""
	
	inits = None
	"""Player's initials."""
	
	date = None
	"""String date representation of this score, using :func:`time.asctime`."""
	
	key = None
	"""Object value used to uniquely identify this score."""
	
	name = None
	"""Player's name, such as `Player 1`."""
	
	title = None
	"""Title for this score, such as `Grand Champion`."""

	def __init__(self, score=None, inits=None, name=None, key=None):
		self.score = score
		self.inits = inits
		self.name = name
		self.key = key
		self.date = time.asctime()
	
	def __repr__(self):
		return '<%s score=%d inits=%s>' % (self.__class__.__name__, self.score, self.inits)

	def from_dict(self, src):
		"""Populate the high score value from a dictionary.
		Requires `score` and `inits` keys, may include `date`."""
		self.score = src['score']
		self.inits = src['inits']
		if 'date' in src:
			self.date = src['date']
		return self

	def to_dict(self):
		"""Returns a dictionary representation of this high score,
		including `score`, `inits`, and `date`."""
		return {'score':self.score, 'inits':self.inits, 'date':self.date}

	def __cmp__(self, other):
		c = cmp(self.score, other.score)
		if c == 0:
			return cmp(other.date, self.date)
		else:
			return c

class EntrySequenceManager(game.Mode):
	"""A :class:`~procgame.game.Mode` subclass that manages the presentation of :class:`InitialEntryMode`
	in order to prompt the player(s) for new high scores.

	The :attr:`logic` attribute should be set to an instance of :class:`HighScoreLogic`,
	which is used to customize the behavior of the sequence manager.  The behavior of
	this class can be modified by supplying different subclasses of :class:`HighScoreLogic`.

	This mode does not remove itself from the mode queue.
	Set :attr:`finished_handler` to a method to call once the sequence is completed.
	The handler will be called immediately (once this mode is added to the mode queue)
	if there are no high scores to be entered.
	"""

	prompts = None
	active_prompt = None

	logic = None
	"""Set this attribute to an instance of :class:`HighScoreLogic`."""
	
	ready_handler = None
	"""Method taking two objects: this class instance and the :class:`EntryPrompt` to be shown next.
	The implementor must call :meth:`prompt` in order to present the initials entry mode, otherwise
	the sequence will not proceed.  If this attribute is not set then initials entry mode will be
	shown immediately.
	This allows for special displays or interaction before each initials prompt.
	"""

	finished_handler = None
	"""Method taking one parameter, the mode (this object instance)."""

	def mode_started(self):
		self.prompts = self.logic.prompts()
		self.next()

	def next(self):
		if len(self.prompts) > 0:
			self.active_prompt = self.prompts[0]
			del self.prompts[0]
			if self.ready_handler:
				self.ready_handler(self, self.active_prompt)
			else:
				self.prompt()
		else:
			if self.finished_handler != None:
				self.finished_handler(mode=self)
	
	def prompt(self):
		"""To be called externally if using the :attr:`ready_handler`, once that handler has been called.
		Presents the initials entry mode."""
		self.prompt_for_initials(left_text=self.active_prompt.left, right_text=self.active_prompt.right)

	def create_highscore_entry_mode(self, left_text, right_text, entered_handler):
		"""Subclasses can override this to supply their own entry handler."""
		return InitialEntryMode(game=self.game, priority=self.priority+1, left_text=left_text, right_text=right_text, entered_handler=entered_handler)

	def prompt_for_initials(self, left_text, right_text):
		self.highscore_entry = self.create_highscore_entry_mode(left_text, right_text, self.highscore_entered)
		self.add_child_mode(self.highscore_entry)

	def highscore_entered(self, mode, inits):
		self.logic.store_initials(key=self.active_prompt.key, inits=inits)
		self.remove_child_mode(self.highscore_entry) # same as *mode*
		self.next()
