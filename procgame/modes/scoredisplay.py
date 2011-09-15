import pinproc
import struct
import time
import os
import locale
from ..game import Mode
from .. import dmd

class ScoreLayer(dmd.GroupedLayer):
	def __init__(self, width, height, mode):
		super(ScoreLayer, self).__init__(width, height, mode)
		self.mode = mode
	def next_frame(self):
		"""docstring for next_frame"""
		# Setup for the frame.
		self.mode.update_layer()
		return super(ScoreLayer, self).next_frame()


class ScoreDisplay(Mode):
	""":class:`ScoreDisplay` is a mode that provides a DMD layer containing a generic 1-to-4 player score display.  
	To use :class:`ScoreDisplay` simply instantiate it and add it to the mode queue.  A low priority is recommended.
	
	When the layer is asked for its :meth:`~procgame.dmd.Layer.next_frame` the DMD frame is built based on 
	the player score and ball information contained in the :class:`~procgame.game.GameController`.
	
	:class:`ScoreDisplay` uses a number of fonts, the defaults of which are included in the shared DMD resources folder.
	If a font cannot be found then the score may not display properly
	in some states.  Fonts are loaded using :func:`procgame.dmd.font_named`; see its documentation for dealing with
	fonts that cannot be found.
	
	You can substitute your own fonts (of the appropriate size) by assigning the font attributes after initializing
	:class:`ScoreDisplay`.
	"""
	
	font_common = None
	"""Font used for the bottom status line text: ``'BALL 1  FREE PLAY'``.  Defaults to Font07x5.dmd."""
	font_18x12 = None
	"""Defaults to Font18x12.dmd."""
	font_18x11 = None
	"""Defaults to Font18x11.dmd."""
	font_18x10 = None
	"""Defaults to Font18x10.dmd."""
	font_14x10 = None
	"""Defaults to Font14x10.dmd."""
	font_14x9 = None
	"""Defaults to Font14x9.dmd."""
	font_14x8 = None
	"""Defaults to Font14x8.dmd."""
	font_09x5 = None
	"""Defaults to Font09x5.dmd."""
	font_09x6 = None
	"""Defaults to Font09x6.dmd."""
	font_09x7 = None
	"""Defaults to Font09x7.dmd."""
	
	credit_string_callback = None
	"""If non-``None``, :meth:`update_layer` will call it with no parameters to get the credit string (usually FREE PLAY or CREDITS 1 or similar).
	If this method returns the empty string no text will be shown (and any ball count will be centered).  If ``None``, FREE PLAY will be shown."""
	
	def __init__(self, game, priority, left_players_justify="right"):
		super(ScoreDisplay, self).__init__(game, priority)
		self.layer = ScoreLayer(128, 32, self)
		self.font_common = dmd.font_named("Font07x5.dmd")
		self.font_18x12 = dmd.font_named("Font18x12.dmd")
		self.font_18x11 = dmd.font_named("Font18x11.dmd")
		self.font_18x10 = dmd.font_named("Font18x10.dmd")
		self.font_14x10 = dmd.font_named("Font14x10.dmd")
		self.font_14x9 = dmd.font_named("Font14x9.dmd")
		self.font_14x8 = dmd.font_named("Font14x8.dmd")
		self.font_09x5 = dmd.font_named("Font09x5.dmd")
		self.font_09x6 = dmd.font_named("Font09x6.dmd")
		self.font_09x7 = dmd.font_named("Font09x7.dmd")
		self.set_left_players_justify(left_players_justify)
	
	def set_left_players_justify(self, left_players_justify):
		"""Call to set the justification of the left-hand players' scores in a multiplayer game.
		Valid values for ``left_players_justify`` are ``'left'`` and ``'right'``."""
		if left_players_justify == "left":
			self.score_posns = { True: [(0, 0), (128, 0), (0, 11), (128, 11)], False: [(0, -1), (128, -1), (0, 16), (128, 16)] }
		elif left_players_justify == "right":
			self.score_posns = { True: [(75, 0), (128, 0), (75, 11), (128, 11)], False: [(52, -1), (128, -1), (52, 16), (128, 16)] }
		else:
			raise ValueError, "Justify must be right or left."
		self.score_justs = [left_players_justify, 'right', left_players_justify, 'right']
	
	def format_score(self, score):
		"""Returns a string representation of the given score value.
		Override to customize the display of numeric score values."""
		if score == 0:
			return '00'
		else:
			return locale.format("%d", score, True)
	
	def font_for_score_single(self, score):
		"""Returns the font to be used for displaying the given numeric score value in a single-player game."""
		if score <   1e10:
			return self.font_18x12
		elif score < 1e11:
			return self.font_18x11
		else:
			return self.font_18x10
		
	def font_for_score(self, score, is_active_player):
		"""Returns the font to be used for displaying the given numeric score value in a 2, 3, or 4-player game."""
		if is_active_player:
			if score < 1e7:
				return self.font_14x10
			if score < 1e8:
				return self.font_14x9
			else:
				return self.font_14x8
		else:
			if score < 1e7:
				return self.font_09x7
			if score < 1e8:
				return self.font_09x6
			else:
				return self.font_09x5

	def pos_for_player(self, player_index, is_active_player):
		return self.score_posns[is_active_player][player_index]
	
	def justify_for_player(self, player_index):
		return self.score_justs[player_index]
	
	def update_layer(self):
		"""Called by the layer to update the score layer for the present game state."""
		self.layer.layers = []
		if len(self.game.players) <= 1:
			self.update_layer_1p()
		else:
			self.update_layer_4p()
		# Common: Add the "BALL X ... FREE PLAY" footer.
		common = dmd.TextLayer(128/2, 32-6, self.font_common, "center")
		
		credit_str = 'FREE PLAY'
		if self.credit_string_callback:
			credit_str = self.credit_string_callback()
		if self.game.ball == 0:
			common.set_text(credit_str)
		elif len(credit_str) > 0:
			common.set_text("BALL %d      %s" % (self.game.ball, credit_str))
		else:
			common.set_text("BALL %d" % (self.game.ball))
		self.layer.layers += [common]

	def update_layer_1p(self):
		if self.game.current_player() == None:
			score = 0 # Small hack to make *something* show up on startup.
		else:
			score = self.game.current_player().score
		layer = dmd.TextLayer(128/2, 5, self.font_for_score_single(score), "center")
		layer.set_text(self.format_score(score))
		self.layer.layers += [layer]

	def update_layer_4p(self):
		for i in range(len(self.game.players[:4])): # Limit to first 4 players for now.
			score = self.game.players[i].score
			is_active_player = (self.game.ball > 0) and (i == self.game.current_player_index)
			font = self.font_for_score(score=score, is_active_player=is_active_player)
			pos = self.pos_for_player(player_index=i, is_active_player=is_active_player)
			justify = self.justify_for_player(player_index=i)
			layer = dmd.TextLayer(pos[0], pos[1], font, justify)
			layer.set_text(self.format_score(score))
			self.layer.layers += [layer]
		pass

	def mode_started(self):
		pass

	def mode_stopped(self):
		pass
