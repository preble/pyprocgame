import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame
import pinproc
from procgame import *
import locale
import yaml

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

config_path = "../shared/config/JD.yaml"
dmd.font_path.append('../shared/dmd')


class TestGame(game.GameController):
	"""docstring for TestGame"""
	def __init__(self, machineType):
		super(TestGame, self).__init__(machineType)
		self.dmd = dmd.DisplayController(self, width=128, height=32)
		self.desktop = procgame.desktop.Desktop()
		self.get_keyboard_events = self.desktop.get_keyboard_events
		
	def setup(self):
		"""docstring for setup"""
		self.load_config(config_path)
		self.highscore_entry = highscoreentry.HighScoreEntry(game=self, priority=1, left_text='Player 1', right_text='High Score #2', entered_handler=self.highscore_entered)
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
	
	def highscore_entered(self, mode, inits):
		self.modes.remove(mode)
		print "Got high score entry:", inits

def main():
	config = yaml.load(open(config_path, 'r'))
	machineType = config['PRGame']['machineType']
	#machineType = 'wpc'
	print machineType
	config = 0
	game = None
	try:
	 	game = TestGame(machineType)
		game.setup()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()
