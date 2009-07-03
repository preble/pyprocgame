import procgame
from procgame import *
from threading import Thread
import sys
import random
import string
import time
import chuckctrl
import locale
import math

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

fonts_path = "/Users/adam/Documents/DMD/"
font_tiny7 = dmd.Font(fonts_path+"04B-03-7px.dmd")
font_jazz18 = dmd.Font(fonts_path+"Jazz18-18px.dmd")

class Attract(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(Attract, self).__init__(game, 1)
		self.layer = dmd.GroupedLayer(128, 32, [])
		press_start = dmd.TextLayer(128/2, 7, font_jazz18, "center")
		press_start.set_text("Press Start")
		l = dmd.ScriptedLayer(128, 32, [{'seconds':1.0, 'layer':press_start}, {'seconds':0.5, 'layer':None}])
		self.layer.layers += [l]
		l = dmd.TextLayer(128/2, 32-7, font_tiny7, "center")
		l.set_text("Free Play")
		self.layer.layers += [l]
		

	def mode_topmost(self):
		self.game.lamps.gi01.schedule(schedule=0xffffffff, cycle_seconds=0, now=False)
		self.game.lamps.gi02.disable()
		self.game.lamps.startButton.schedule(schedule=0x00000fff, cycle_seconds=0, now=False)
		self.game.set_status("Press Start")
		for name in ['popperL', 'popperR']:
			if self.game.switches[name].is_open():
				self.game.coils[name].pulse()
		for name in ['shooterL', 'shooterR']:
			if self.game.switches[name].is_closed():
				self.game.coils[name].pulse()

	def mode_started(self):
		self.game.dmd.layers.insert(0, self.layer)

	def mode_stopped(self):
		self.game.dmd.layers.remove(self.layer)
		
	def mode_tick(self):
		#self.layer.layers[0].enabled = (int(1.5 * time.time()) % 2) == 0
		pass
					
	def sw_popperL_open_for_500ms(self, sw): # opto!
		self.game.coils.popperL.pulse(20)

	def sw_popperR_open_for_500ms(self, sw): # opto!
		self.game.coils.popperR.pulse(20)

	def sw_shooterL_closed_for_500ms(self, sw):
		self.game.coils.shooterL.pulse(20)

	def sw_shooterR_closed_for_500ms(self, sw):
		self.game.coils.shooterR.pulse(20)

	def sw_startButton_closed(self, sw):
		self.game.set_status("Got start!")
		self.game.modes.add(StartOfBall(self.game))
		self.game.modes.remove(self)
		self.game.sound.beep()
		self.game.ball = 1
		self.game.add_player()
		return True


class StartOfBall(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(StartOfBall, self).__init__(game, 2)
		self.game_display = GameDisplay(self.game)

	def mode_started(self):
		self.game.modes.add(self.game_display)
		self.game.enable_flippers(enable=True)
		self.game.lamps.gi02.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
		self.game.lamps.startButton.disable()
		if self.game.switches.trough6.is_open():
			self.game.set_status("Pulsing trough")
			self.game.coils.trough.pulse(20)
		dropTargets = procgame.modes.BasicDropTargetBank(self.game, priority=8, prefix='dropTarget', letters='JUDGE')
		#dropTargets = procgame.modes.ProgressiveDropTargetBank(self.game, priority=8, prefix='dropTarget', letters='JUDGE', advance_switch='subwayEnter1')
		dropTargets.on_advance = self.on_droptarget_advance
		dropTargets.on_completed = self.on_droptarget_completed
		self.game.modes.add(dropTargets)
	
	def mode_stopped(self):
		self.game.enable_flippers(enable=False)
		self.game.modes.remove(self.game_display)
	
	def on_droptarget_advance(self, mode):
		self.game.sound.beep()
		self.game.score(5000)
		pass
		
	def on_droptarget_completed(self, mode):
		self.game.sound.beep()
		self.game.score(20000)
		pass
	
	def sw_trough1_open_for_500ms(self, sw):
		in_play = self.game.is_ball_in_play()
		if not in_play:
			self.game.set_status("Ball dropped")
			trough6_closed = self.game.switches.trough6.is_open()
			shooterR_closed = self.game.switches.shooterR.is_closed()
			if trough6_closed and not shooterR_closed:
				self.game.set_status("Pulsing next ball")
				self.game.coils.trough.pulse(20)
		# TODO: What if the ball doesn't make it into the shooter lane?
		#       We should check for it on a later mode_tick() and possibly re-pulse.
		return True
	
	def sw_popperL_open(self, sw):
		self.game.set_status("Left popper!")
		
	def sw_popperL_open_for_500ms(self, sw): # opto!
		self.game.coils.popperL.pulse(20)

	def sw_popperR_open(self, sw):
		self.game.set_status("Right popper!")

	def sw_popperR_open_for_500ms(self, sw): # opto!
		self.game.coils.popperR.pulse(20)

	def sw_startButton_closed(self, sw):
		# Todo: Add players to game
		return True
	
	def sw_fireL_closed(self, sw):
		if self.game.switches.shooterL.is_closed():
			self.game.coils.shooterL.pulse(50)
	
	def sw_fireR_closed(self, sw):
		if self.game.switches.shooterR.is_closed():
			self.game.coils.shooterR.pulse(50)

	def sw_startButton_closed(self, sw):
		if self.game.ball == 1:
			p = self.game.add_player()
			self.game.set_status(p.name + " added!")
	def sw_startButton_closed_for_2s(self, sw):
		if self.game.ball > 1:
			self.game.set_status("Reset!")
			self.game.reset()
			return True
		
	def sw_outlaneL_closed(self, sw):
		self.game.sound.play('outlane')
	def sw_outlaneR_closed(self, sw):
		self.game.sound.play('outlane')

class GameDisplay(game.Mode):
	"""Displays the score and other game state information on the DMD."""
	def __init__(self, game):
		super(GameDisplay, self).__init__(game, 0)
		self.status_layer = dmd.TextLayer(0, 0, font_tiny7)
		self.game_layer = dmd.TextLayer(0, 25, font_tiny7)
		self.score_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center")
		self.score_layer.set_text("1,000,000")
		self.layer = dmd.GroupedLayer(128, 32, [self.score_layer, self.status_layer, self.game_layer])

	def mode_started(self):
		self.game.dmd.layers.insert(0, self.layer)

	def mode_stopped(self):
		self.game.dmd.layers.remove(self.layer)

	def mode_tick(self):
		if len(self.game.players) > 0:
			self.score_layer.set_text(commatize(self.game.current_player().score))
			self.game_layer.set_text('%s - Ball %d' % (self.game.current_player().name, self.game.ball))
		self.game.dmd.update()

class PopupDisplay(game.Mode):
	"""Displays a pop-up message on the DMD."""
	def __init__(self, game):
		super(PopupDisplay, self).__init__(game, 0)
		self.status_layer = dmd.TextLayer(128/2, 32-7, font_tiny7, "center")
	
	def set_text(self, text, seconds=5):
		self.status_layer.set_text(text, seconds)
	
	def mode_started(self):
		self.game.dmd.layers.insert(0, self.status_layer)
		
	def mode_stopped(self):
		self.game.dmd.layers.remove(self.status_layer)
	
	def mode_tick(self):
		#if len(self.game.modes.modes) > 0:
		#	self.mode_layer.set_text('Topmost: '+str(self.game.modes.modes[0].status_str()))
		self.game.dmd.update()

def commatize(n):
	return locale.format("%d", n, True)
	
class SoundController(object):
	"""docstring for TestGame"""
	def __init__(self, delegate):
		super(SoundController, self).__init__()
		#self.chuck = chuckctrl.ChuckProcess(self)
	def beep(self):
		self.play('chime')
	def play(self, name):
		#self.chuck.add_shred('sound/'+name)
		#self.chuck.poll()
		pass
	def on_add_shred(self, num, name):
		pass
	def on_rm_shred(self, num, name):
		pass

class TestGame(game.GameController):
	"""docstring for TestGame"""
	def __init__(self, machineType):
		super(TestGame, self).__init__(machineType)
		self.sound = SoundController(self)
		self.dmd = dmd.DisplayController(self.proc, width=128, height=32)
		self.popup = PopupDisplay(self)
		
	def setup(self):
		"""docstring for setup"""
		self.load_config('../libpinproc/examples/pinproctest/JD.yaml')
		print("Initial switch states:")
		for sw in self.switches:
			print("  %s:\t%s" % (sw.name, sw.state_str()))
		self.reset()
		
	def reset(self):
		super(TestGame, self).reset()
		self.modes.add(self.popup)
		self.modes.add(Attract(self))
		
	def is_ball_in_play(self):
		return self.switches.trough1.is_closed() # TODO: Check other trough switches.
	
	def set_status(self, text):
		self.popup.set_text(text)
		print(text)
	
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