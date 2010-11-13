import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import pinproc
from procgame import *
from threading import Thread
import random
import string
import time
import locale
import math
import copy

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

config_path = "JD.yaml"

class ScoreTester(game.Mode):
	left_players_justify_left = True
	def sw_flipperLwL_active(self, sw):
		self.game.score(random.randint(0, 100000)*10)
		return True
	def sw_flipperLwR_active(self, sw):
		self.game.end_ball()
		return True
	def sw_fireL_active(self, sw):
		self.left_players_justify_left = not self.left_players_justify_left
		if self.left_players_justify_left:
			self.game.score_display.set_left_players_justify("left")
		else:
			self.game.score_display.set_left_players_justify("right")
		return True

class TestGame(game.BasicGame):
	"""docstring for TestGame"""
	
	def setup(self):
		"""docstring for setup"""
		self.load_config(config_path)
		self.reset()
		
		self.start_game()
		
		for i in range(4):
			self.add_player()
			self.players[i].score = random.randint(0, 1e5)*10

		self.current_player_index = 0#random.randint(0, 3)
		
		self.start_ball()
		
	def reset(self):
		super(TestGame, self).reset()
		self.modes.add(ScoreTester(self, 5))
		# Make sure flippers are off, especially for user-initiated resets.
		self.enable_flippers(enable=False)

def main():
	game = None
	try:
	 	game = TestGame(pinproc.MachineTypeWPC)
		game.setup()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()
