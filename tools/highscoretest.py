import sys
import os
import locale
import yaml
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
from procgame import *

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

config_path = "JD.yaml"

class TestGame(game.BasicGame):
	"""docstring for TestGame"""
	def __init__(self, machineType):
		super(TestGame, self).__init__(machineType)
		
	def setup(self):
		"""docstring for setup"""
		self.load_config(config_path)
		self.highscore_entry = modes.HighScoreEntry(game=self, priority=2, left_text='Player 1', right_text='High Score #2', entered_handler=self.highscore_entered)
		self.reset()
		
	def reset(self):
		super(TestGame, self).reset()
		self.modes.add(self.highscore_entry)
		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)
		
	def highscore_entered(self, mode, inits):
		self.modes.remove(mode)
		print "Got high score entry:", inits

def main():
	config = game.config_named(config_path)
	machine_type = config['PRGame']['machineType']
	del config
	test_game = None
	try:
	 	test_game = TestGame(machine_type)
		test_game.setup()
		test_game.run_loop()
	finally:
		del test_game

if __name__ == '__main__': main()
