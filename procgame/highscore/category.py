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

	score_for_player = lambda category, player: player.score
	"""Method used to fetch the high score *score* value for a given category and player.
	The default value is::
	
	    lambda category, player: player.score
	
	"""

	default_scores = [HighScore(score=5000000,inits='GSS'),HighScore(score=4000000,inits='ASP'),HighScore(score=3000000,inits='JRP'),HighScore(score=2000000,inits='JAG'),HighScore(score=1000000,inits='JTW')]
	"""List of populated :class:`HighScore` objects representing the default high scores for this category."""

	titles = ['Grand Champion', 'High Score #1', 'High Score #2', 'High Score #3', 'High Score #4']
	"""There must be a title for each high score slot desired for this category."""

	def load_from_game(self, game):
		"""Loads :attr:`scores` from *game* using :attr:`game_data_key`."""
		if self.game_data_key in game.game_data:
			self.scores = list()
			for d in game.game_data[self.game_data_key]:
				self.scores.append(HighScore().from_dict(d))
		else:
			self.scores = list(self.default_scores)

		for score in self.scores:
			score.key = None # No key for existing scores.

	def save_to_game(self, game):
		"""Saves :attr:`scores` to *game* using :attr:`game_data_key`."""
		self.scores = self.scores[0:len(self.titles)]
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

	def prompts(self):
		prompts = list()
		# Create keyed_prompts:
		keyed_prompts = {}
		for category in self.categories:
			category.scores = sorted(category.scores, reverse=True) # Reverse to sort from high to low.
			for index, score in enumerate(category.scores[0:len(category.titles)]):
				if score.inits == None:
					new_title = category.titles[index]
					if score.key in keyed_prompts:
						existing = keyed_prompts[score.key]
						existing['right'].append(new_title)
					else:
						keyed_prompts[score.key] = {'left':score.name, 'right':[new_title]}
		# Process keyed_prompts into prompts:
		for key in keyed_prompts:
			d = keyed_prompts[key]
			d.update({'key':key})
			prompts.append(d)
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
