import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame
import pinproc
from deadworld import *
from procgame import *
from threading import Thread
import random
import string
import time
import locale
import math
import copy
import pygame
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((300, 20))
pygame.display.set_caption('scoredisplaytest.py - Press CTRL-C to exit')

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

config_path = "../shared/config/JD.yaml"
fonts_path = "../shared/dmd/"

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

class TestGame(game.GameController):
	"""docstring for TestGame"""
	def __init__(self, machineType):
		super(TestGame, self).__init__(machineType)
		self.dmd = dmd.DisplayController(self, width=128, height=32)
		self.score_display = scoredisplay.ScoreDisplay(self, 1)
		
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
		self.modes.add(self.score_display)
		self.modes.add(ScoreTester(self, 5))
		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)
		
	def dmd_event(self):
		"""Called by the GameController when a DMD event has been received."""
		self.dmd.update()

	def score(self, points):
		p = self.current_player()
		p.score += points

def main():
	machineType = 'wpc'
	game = None
	try:
	 	game = TestGame(machineType)
		game.setup()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()
