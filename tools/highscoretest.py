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

class HighScoreEntry(game.Mode):
	def __init__(self, game, priority, player, place):
		super(HighScoreEntry, self).__init__(game, priority)
		
		self.font = dmd.Font(fonts_path+'Font07x5.dmd')
		
		self.layer = dmd.GroupedLayer(128, 32)
		self.layer.opaque = True
		self.layer.layers = []
		
		tophalf = dmd.Frame(width=128, height=16)
		self.font.draw(tophalf, player, 0, 0)
		self.font.draw(tophalf, "High Score #%d" % (place), 0, 8)
		tophalf_layer = dmd.FrameLayer(opaque=False, frame=tophalf)
		tophalf_layer.set_target_position(0, 0)
		self.layer.layers += [tophalf_layer]
		
		self.lowerhalf_layer = dmd.AnimatedLayer(opaque=False, hold=True)
		self.lowerhalf_layer.set_target_position(0, 16)
		self.layer.layers += [self.lowerhalf_layer]
		
		self.letters = []
		for idx in range(26):
			self.letters += [chr(ord('A')+idx)]
		self.current_letter_index = 0
		self.animate_to_index(0)
	
	def mode_started(self):
		pass
		
	def mode_stopped(self):
		pass
				
	def animate_to_index(self, new_index, inc = 0):
		letter_spread = 9
		letter_width = 7
		if inc < 0:
			rng = range(inc * letter_width, 1)
		elif inc > 0:
			rng = range(inc * letter_width)[::-1]
		else:
			rng = [0]
		print rng
		for x in rng:
			frame = dmd.Frame(width=128, height=16)
			frame.fill_rect(64-5, 0, 10, 14, 1)
			frame.fill_rect(64-3, 2, 6, 10, 0)
			for offset in range(-6, 7):
				index = new_index - offset
				print "Index %d  len=%d" % (index, len(self.letters))
				if index < 0:
					index = len(self.letters) + index
				elif index >= len(self.letters):
					index = index - len(self.letters)
				(w, h) = self.font.size(self.letters[index])
				print "Drawing %d w=%d" % (index, w)
				self.font.draw(frame, self.letters[index], 128/2 - offset * letter_spread - letter_width/2 + x, 2)
			self.lowerhalf_layer.frames += [frame]
		self.current_letter_index = new_index
		
	def letter_increment(self, inc):
		new_index = (self.current_letter_index + inc)
		if new_index < 0:
			new_index = len(self.letters) + new_index
		elif new_index >= len(self.letters):
			new_index = new_index - len(self.letters)
		print("letter_increment %d + %d = %d" % (self.current_letter_index, inc, new_index))
		self.animate_to_index(new_index, inc)
		
	def sw_flipperLwL_active(self, sw):
		self.letter_increment(-1)
		return False
	def sw_flipperLwR_active(self, sw):
		self.letter_increment(1)
		return False
	def sw_startButton_active(self, sw):
		self.letter_accept()
		return False

class TestGame(game.GameController):
	"""docstring for TestGame"""
	def __init__(self, machineType):
		super(TestGame, self).__init__(machineType)
		self.dmd = dmd.DisplayController(self, width=128, height=32)
		
	def setup(self):
		"""docstring for setup"""
		self.load_config(config_path)
		self.highscore_entry = HighScoreEntry(self, 1, "Player 1", 2)
		self.reset()
		
	def reset(self):
		super(TestGame, self).reset()
		self.modes.add(self.highscore_entry)
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
