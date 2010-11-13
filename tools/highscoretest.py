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
		script = []
		
		# Cheating a bit here to make the score display have a transition, since it it always on:
		script.append({'seconds':3.0, 'layer':self.game.score_display.layer})
		self.game.score_display.layer.transition = dmd.PushTransition(direction='south')
		
		for frame in highscore.generate_highscore_frames(self.game.highscore_categories):
			layer = dmd.FrameLayer(frame=frame)
			layer.transition = dmd.PushTransition(direction='south')
			script.append({'seconds':2.0, 'layer':layer})
		
		self.layer = dmd.ScriptedLayer(width=128, height=32, script=script)
		
		# Opaque allows transitions between scripted layer 'frames' to work:
		self.layer.opaque=True


class TestGame(game.BasicGame):
	
	highscore_categories = None
	
	def __init__(self, machine_type):
		super(TestGame, self).__init__(machine_type)
		
	def setup(self):
		self.load_config(config_path)
		self.desktop.add_key_map(ord('q'), self.switches.exit.number)
		
		self.highscore_categories = []
		
		cat = highscore.HighScoreCategory()
		# because we don't have a game_data template:
		cat.scores = [highscore.HighScore(score=5000000,inits='GSS'),\
					  highscore.HighScore(score=4000000,inits='ASP'),\
					  highscore.HighScore(score=3000000,inits='JRP'),\
					  highscore.HighScore(score=2000000,inits='JAG'),\
					  highscore.HighScore(score=1000000,inits='JTW')]
		cat.game_data_key = 'ClassicHighScoreData'
		self.highscore_categories.append(cat)
		
		cat = highscore.HighScoreCategory()
		cat.game_data_key = 'LoopsHighScoreData'
		# because we don't have a game_data template:
		cat.scores = [highscore.HighScore(score=5,inits='GSS')]
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
		seq_manager.ready_handler = self.highscore_entry_ready_to_prompt
		seq_manager.finished_handler = self.highscore_entry_finished
		
		seq_manager.logic = highscore.CategoryLogic(game=self, categories=self.highscore_categories)
		self.modes.add(seq_manager)
	
	def add_attract(self):
		self.attract = Attract(game=self, priority=8)
		self.modes.add(self.attract)
	
	def highscore_entry_ready_to_prompt(self, mode, prompt):
		banner_mode = game.Mode(game=self, priority=8)
		markup = dmd.MarkupFrameGenerator()
		markup.font_plain = dmd.font_named('Font09Bx7.dmd')
		markup.font_bold = dmd.font_named('Font13Bx9.dmd')
		text = '[Great Score]\n#%s#' % (prompt.left.upper()) # we know that the left is the player name
		frame = markup.frame_for_markup(markup=text, y_offset=0)
		frame_layer = dmd.FrameLayer(frame=frame)
		frame_layer.blink_frames = 10
		banner_mode.layer = dmd.ScriptedLayer(width=128, height=32, script=[{'seconds':3.0, 'layer':frame_layer}])
		banner_mode.layer.on_complete = lambda: self.highscore_banner_complete(banner_mode=banner_mode, highscore_entry_mode=mode)
		self.modes.add(banner_mode)
	
	def highscore_banner_complete(self, banner_mode, highscore_entry_mode):
		self.modes.remove(banner_mode)
		highscore_entry_mode.prompt()
	
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
