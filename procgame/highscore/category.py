from sequence import *

class HighScoreCategory:

	game_data_key = None
	"""Key to this high score category's data within :attr:`game.GameController.game_data`."""

	scores = None
	"""List of :class:`HighScore` objects for this category.  Populated by :meth:`load_from_game`."""

	score_suffix_singular = ''
	"""Singular suffix to append to string representations of high scores in this category, such as ``point``.
	Used by :func:`generate_highscore_frames`."""
	score_suffix_plural = ''
	"""Plural suffix to append to string representations of high scores in this category, such as ``points``.
	Used by :func:`generate_highscore_frames`."""

	score_for_player = None
	"""Method used to fetch the high score *score* value for a given :class:`~procgame.game.Player`.
	The default value is::
	
	    lambda player: player.score
	
	"""

	titles = ['Grand Champion', 'High Score #1', 'High Score #2', 'High Score #3', 'High Score #4']
	"""There must be a title for each high score slot desired for this category."""
	
	def __init__(self):
		self.score_for_player = lambda player: player.score

	def load_from_game(self, game):
		"""Loads :attr:`scores` from *game* using :attr:`game_data_key`."""
		if self.game_data_key in game.game_data:
			self.scores = list()
			for d in game.game_data[self.game_data_key]:
				self.scores.append(HighScore().from_dict(d))
		else:
			game.logger.warning('HighScoreCategory.load_from_game(): game_data_key %s not found in game_data.', self.game_data_key)

		for score in self.scores:
			score.key = None # No key for existing scores.

	def save_to_game(self, game):
		"""Saves :attr:`scores` to *game* using :attr:`game_data_key`."""
		save_scores = map(lambda s: s.to_dict(), self.scores)
		game.game_data[self.game_data_key] = save_scores

class CategoryDrivenDataHelper:
	"""Utility class used by :class:`CategoryLogic`."""
	
	game = None

	categories = None

	def __init__(self, game, categories):
		self.game = game
		self.categories = categories;
		self.load_from_game_data()

	def load_from_game_data(self):
		for category in self.categories:
			category.load_from_game(self.game)

	def save_to_game_data(self):
		for category in self.categories:
			category.save_to_game(self.game)

	def add_placeholder(self, category, score, name):
		"""Uses the name as the key."""
		hs = HighScore(score=score, inits=None, name=name, key=name)
		category.scores.append(hs)
		category.scores = sorted(category.scores, reverse=True) # Reverse to sort from high to low.
		category.scores = category.scores[0:len(category.titles)]

	def prompts(self):
		prompts = list()
		# Create keyed_prompts:
		keyed_prompts = {}
		for category in self.categories:
			for index, score in enumerate(category.scores):
				if score.inits == None:
					new_title = category.titles[index]
					if score.key in keyed_prompts:
						existing = keyed_prompts[score.key]
						existing.right.append(new_title)
					else:
						keyed_prompts[score.key] = EntryPrompt(left=score.name, right=[new_title])
		# Process keyed_prompts into prompts:
		for key in keyed_prompts:
			prompt = keyed_prompts[key]
			prompt.key = key
			prompts.append(prompt)
		return prompts

	def set_inits_by_key(self, key, inits):
		for category in self.categories:
			for score in category.scores:
				if score.key == key:
					score.inits = inits


class CategoryLogic(HighScoreLogic):
	"""Subclass of :class:`HighScoreLogic`.  Implements a variable number of scoreboards using categories.
	
	*categories* is a list of :class:`HighScoreCategory` instances which will be checked for 
	qualifying high scores.
	"""

	game = None
	data = None
	categories = None

	def __init__(self, game, categories):
		self.game = game
		self.categories = categories

	def prompts(self):
		self.data = CategoryDrivenDataHelper(game=self.game, categories=self.categories)
		for category in self.categories:
			for player in self.game.players:
				self.data.add_placeholder(category=category, score=category.score_for_player(player), name=player.name)
		return self.data.prompts()

	def store_initials(self, key, inits):
		self.data.set_inits_by_key(key=key, inits=inits)
		self.data.save_to_game_data()
