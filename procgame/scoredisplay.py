import pinproc
import struct
import time
import os
import locale
from game import *
from dmd import *

class ScoreLayer(GroupedLayer):
	def __init__(self, width, height, mode):
		super(ScoreLayer, self).__init__(width, height, mode)
		self.mode = mode
	def next_frame(self):
		"""docstring for next_frame"""
		# Setup for the frame.
		self.mode.update_layer()
		return super(ScoreLayer, self).next_frame()


class ScoreDisplay(Mode):
	"""After instantiation the ScoreDisplay.layer should be added to the DisplayController."""
	def __init__(self, game, priority, left_players_justify="right"):
		super(ScoreDisplay, self).__init__(game, priority)
		self.layer = ScoreLayer(128, 32, self)
		font_path = "../shared/dmd"
		self.font_common = Font(font_path+"/Font07x5.dmd")
		self.font_18x12 = Font(font_path+"/Font18x12.dmd")
		self.font_18x11 = Font(font_path+"/Font18x11.dmd")
		self.font_18x10 = Font(font_path+"/Font18x10.dmd")
		self.font_14x10 = Font(font_path+"/Font14x10.dmd")
		self.font_14x9 = Font(font_path+"/Font14x9.dmd")
		self.font_14x8 = Font(font_path+"/Font14x8.dmd")
		self.font_09x5 = Font(font_path+"/Font09x5.dmd")
		self.font_09x6 = Font(font_path+"/Font09x6.dmd")
		self.font_09x7 = Font(font_path+"/Font09x7.dmd")
		self.set_left_players_justify(left_players_justify)
	
	def set_left_players_justify(self, left_players_justify):
		if left_players_justify == "left":
			self.score_posns = { True: [(0, 0), (128, 0), (0, 11), (128, 11)], False: [(0, -1), (128, -1), (0, 16), (128, 16)] }
		elif left_players_justify == "right":
			self.score_posns = { True: [(75, 0), (128, 0), (75, 11), (128, 11)], False: [(52, -1), (128, -1), (52, 16), (128, 16)] }
		else:
			raise ValueError, "Justify must be right or left."
		self.score_justs = [left_players_justify, 'right', left_players_justify, 'right']
	
	def format_score(self, score):
		if score == 0:
			return '00'
		else:
			return locale.format("%d", score, True)
	
	def font_for_score_single(self, score):
		if score <   1e10:
			return self.font_18x12
		elif score < 1e11:
			return self.font_18x11
		else:
			return self.font_18x10
	def font_for_score(self, score, is_active_player):
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
		"""docstring for update_layer"""
		self.layer.layers = []
		if len(self.game.players) <= 1:
			self.update_layer_1p()
		else:
			self.update_layer_4p()
		# Common: Add the "BALL X ... FREE PLAY" footer.
		common = TextLayer(128/2, 32-6, self.font_common, "center")
		if self.game.ball == 0:
			common.set_text("FREE PLAY")
		else:
			common.set_text("BALL %d      FREE PLAY" % (self.game.ball))
		self.layer.layers += [common]

	def update_layer_1p(self):
		"""docstring for update_layer_1p"""
		if self.game.current_player() == None:
			score = 0 # Small hack to make *something* show up on startup.
		else:
			score = self.game.current_player().score
		layer = TextLayer(128/2, 5, self.font_for_score_single(score), "center")
		layer.set_text(self.format_score(score))
		self.layer.layers += [layer]

	def update_layer_4p(self):
		"""docstring for update_layer_4p"""
		for i in range(len(self.game.players[:4])): # Limit to first 4 players for now.
			score = self.game.players[i].score
			is_active_player = (self.game.ball > 0) and (i == self.game.current_player_index)
			font = self.font_for_score(score=score, is_active_player=is_active_player)
			pos = self.pos_for_player(player_index=i, is_active_player=is_active_player)
			justify = self.justify_for_player(player_index=i)
			layer = TextLayer(pos[0], pos[1], font, justify)
			layer.set_text(self.format_score(score))
			self.layer.layers += [layer]
		pass

	def mode_started(self):
		pass

	def mode_stopped(self):
		pass
