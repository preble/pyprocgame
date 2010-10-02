import sys
import os
import locale
import time
import yaml
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
from procgame import *

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

config_path = "JD.yaml"

class BallEnder(game.Mode):
	"""The exit switch is used to end each ball."""
	def sw_exit_active(self, sw):
		self.game.current_player().score += 350000
		self.game.end_ball()

class BaseGameMode(game.Mode):
	"""A minimal game mode to enable starting a game."""
	def sw_startButton_active(self, sw):
		if self.game.ball == 0:
			self.game.start_game()
			self.game.add_player()
			self.game.start_ball()
		elif self.game.ball == 1:
			p = self.game.add_player()
			self.game.set_status(p.name + " added!")
		else:
			self.game.set_status("Hold for 2s to reset.")

	def sw_startButton_active_for_2s(self, sw):
		if self.game.ball > 1:
			self.game.set_status("Reset!")
			self.game.reset()
			return True

class Attract(game.Mode):
	def mode_started(self):
		# Create a ScriptedLayer with frames for each of the high scores:
		script = list()
		for frame in highscore.generate_highscore_frames(self.game.highscore_categories):
			layer = dmd.FrameLayer(frame=frame)
			script.append({'seconds':2.0, 'layer':layer})
		self.layer = dmd.ScriptedLayer(width=128, height=32, script=script)

class TestGame(game.BasicGame):
	
	highscore_categories = None
	
	def __init__(self, machine_type):
		super(TestGame, self).__init__(machine_type)
		
	def setup(self):
		self.load_config(config_path)
		self.desktop.add_key_map(ord('q'), self.switches.exit.number)
		
		self.highscore_categories = []
		
		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'ClassicHighScoreData'
		self.highscore_categories.append(cat)
		
		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'LoopsHighScoreData'
		cat.default_scores = [highscore.HighScore(score=5,inits='GSS')]
		cat.titles = ['Loop Champ']
		cat.score_suffix_singular = ' loop'
		cat.score_suffix_plural = ' loops'
		self.highscore_categories.append(cat)
		
		for category in self.highscore_categories:
			category.load_from_game(self)
		
		self.reset()
		
	def reset(self):
		super(TestGame, self).reset()
		self.modes.add(BaseGameMode(game=self, priority=1))
		self.modes.add(BallEnder(game=self, priority=1))
		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)
		self.add_attract()
	
	def game_started(self):
		self.modes.remove(self.attract)
		self.attract = None
	
	def game_ended(self):
		seq_manager = highscore.EntrySequenceManager(game=self, priority=2)
		seq_manager.finished_handler = self.highscore_entry_finished
		
		seq_manager.logic = highscore.CategoryLogic(game=self, categories=self.highscore_categories)
		self.modes.add(seq_manager)
	
	def add_attract(self):
		self.attract = Attract(game=self, priority=8)
		self.modes.add(self.attract)
	
	def highscore_entry_finished(self, mode):
		self.modes.remove(mode)
		self.add_attract()
	
	def set_status(self, text):
		self.dmd.set_message(text, 3)
		print(text)
	

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
