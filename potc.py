import procgame
import pinproc
from procgame import *
from threading import Thread
import sys
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
pygame.display.set_caption('POTC - Press CTRL-C to exit')
locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

config_path = "../shared/config/POTC.yaml"
fonts_path = "../shared/dmd/"
sound_path = "../shared/sound/"
font_tiny7 = dmd.Font(fonts_path+"04B-03-7px.dmd")
font_jazz18 = dmd.Font(fonts_path+"Jazz18-18px.dmd")

class Attract(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(Attract, self).__init__(game, 1)
		self.layer = dmd.GroupedLayer(128, 32, [])
		press_start = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("Press Start")
		proc_banner = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("pyprocgame")
		splash = dmd.FrameLayer(opaque=True, frame=dmd.Animation().load(fonts_path+'Splash.dmd').frames[0])
		l = dmd.ScriptedLayer(128, 32, [{'seconds':2.0, 'layer':splash}, {'seconds':2.0, 'layer':press_start}, {'seconds':2.0, 'layer':proc_banner}])
		self.layer.layers += [l]
		l = dmd.TextLayer(128/2, 32-7, font_tiny7, "center")
		#l.set_text("Free Play")
		self.layer.layers += [l]

	def mode_topmost(self):
		self.game.lamps.startButton.schedule(schedule=0x00000fff, cycle_seconds=0, now=False)

	def mode_started(self):
		self.game.lamps.startButton.schedule(schedule=0x00000fff, cycle_seconds=0, now=False)
		#self.game.lamps.gi01.pulse(0)
		#self.game.lamps.gi02.disable()
		#for name in ['topCenterVUK', 'popEject']:
		#	if self.game.switches[name].is_open():
		#		self.game.coils[name].pulse()
		for name in ['topCenterVUK', 'shooterR']:
			if self.game.switches[name].is_closed():
				self.game.coils[name].pulse()
		for name in ['popEject']:
			if self.game.switches[name].is_closed():
				self.game.coils[name].pulse(40)
		for name in ['chestLock']:
			if self.game.switches[name].is_closed():
				self.game.coils[name].pulse(250)
		self.game.dmd.layers.insert(0, self.layer)

	def mode_stopped(self):
		self.game.dmd.layers.remove(self.layer)
		#Remove ball search
	        #self.game.modes.remove(self.game.ball_search)
		
	def mode_tick(self):
		#self.layer.layers[0].enabled = (int(1.5 * time.time()) % 2) == 0
		pass
					
	def sw_enter_closed(self, sw):
		self.game.modes.add(self.game.service_mode)
		# Make sure to remove ball search after adding service mode.
		# Otherwise ball search would get re-added in topmost
	        #self.game.modes.remove(self.game.ball_search)
		return True

	def sw_exit_closed(self, sw):
		return True

	def sw_down_closed(self, sw):
		volume = self.game.sound.volume_down()
		self.game.set_status("Volume Down : " + str(volume))
		return True

	def sw_up_closed(self, sw):
		volume = self.game.sound.volume_up()
		self.game.set_status("Volume Up : " + str(volume))
		return True

	def sw_startButton_closed(self, sw):
		if self.game.is_trough_full(4):
			if self.game.switches.trough1.is_closed():
				self.game.modes.remove(self)
				self.game.start_game()
				self.game.add_player()
				self.game.start_ball()
		else: 
			self.game.set_status("Ball Search!")
			self.game.ball_search.perform_search(5)
		return True


class StartOfBall(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(StartOfBall, self).__init__(game, 2)
		self.game_display = GameDisplay(self.game)
                self.ball_save = procgame.ballsave.BallSave(self.game, self.game.lamps.shootAgain)

	def mode_started(self):
		self.game.modes.add(self.game_display)
		self.game.enable_flippers(enable=True)
		self.game.modes.add(self.ball_save)
		self.auto_plunge = 0
		if self.game.switches.trough1.is_closed():
			self.game.coils.trough.pulse(20)
		self.game.ball_search.enable()
		self.plunder = PlunderDiskMode(self.game, priority=8)
		self.game.modes.add(self.plunder)

	def mode_stopped(self):
		self.game.enable_flippers(enable=False)
		self.game.modes.remove(self.game_display)
		self.game.modes.remove(self.ball_save)
		self.game.ball_search.disable()
		self.game.modes.remove(self.plunder)
	

	def sw_startButton_closed(self, sw):
		if self.game.ball == 1:
			p = self.game.add_player()
			self.game.set_status(p.name + " added!")
		else:
			self.game.set_status("Hold for 2s to reset.")
	def sw_startButton_closed_for_2s(self, sw):
		if self.game.ball > 1:
			self.game.set_status("Reset!")
			self.game.reset()
			return True
		
	def sw_enter_closed(self, sw):
		self.game.modes.add(self.game.service_mode)
		return True

	def sw_trough4_closed_for_500ms(self, sw):
		if (self.ball_save.is_active()):
			self.ball_save.saving_ball()
			self.game.coils.trough.pulse(20)	
		else:
			in_play = self.game.is_ball_in_play()
			if not in_play:
				self.game.end_ball()
				trough1_closed = self.game.switches.trough1.is_closed()
				shooterR_closed = self.game.switches.shooterR.is_closed()
				if trough1_closed and not shooterR_closed and self.game.ball != 0:
					self.game.coils.trough.pulse(20)
			# TODO: What if the ball doesn't make it into the shooter lane?
			#       We should check for it on a later mode_tick() and possibly re-pulse.
		return True

	def sw_topCenterVUK_closed(self, sw): 
		self.game.coils.flasherRearCenter.schedule(schedule=0x55555555, cycle_seconds=1, now=True)

	def sw_topCenterVUK_closed_for_500ms(self, sw): 
		self.game.coils.topCenterVUK.pulse(20)
		self.game.score(2000)

	def sw_popEject_closed_for_500ms(self, sw): 
		self.game.coils.popEject.pulse(40)
		self.game.score(2000)
	
	def sw_chestLock_closed(self, sw): 
		self.game.coils.chestLock.pulse(250)
		self.game.score(2000)
	
	def sw_jackScoopExit_closed(self, sw): 
		self.game.coils.flasherChest.schedule(schedule=0x55555555, cycle_seconds=1, now=True)
		self.game.score(2000)

	def sw_shooterR_open_for_2s(self,sw):
		self.auto_plunge = 1

	def sw_shooterR_closed_for_2s(self,sw):
		if (self.auto_plunge):
			self.game.coils.shooterR.pulse(30)

class PlunderDiskMode(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(PlunderDiskMode, self).__init__(game, priority)
		#self.drop_target_mode = drop_target_mode
		#self.countdown_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center")
		#self.banner_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center")
		#self.layer = dmd.GroupedLayer(128, 32, [self.countdown_layer, self.banner_layer])
		for i in range(1,7):
			switchName = 'plunder' + str(i)
			self.add_switch_handler(name=switchName, event_type='closed', delay=None, handler=self.targetHit)
	
	def mode_started(self):
		self.state = 1;	
		self.update_lamps
		self.game.lamps.backpanel1.pulse(0)
		for i in range(2,8):
			lampName = 'backpanel' + str(i)
			self.game.lamps[lampName].disable()

	def mode_stopped(self):
		#self.game.dmd.layers.remove(self.layer)
		#self.drop_target_mode.animated_reset(1.0)
		#self.game.lamps.multiballJackpot.disable()
		pass

	def update_lamps(self,on):
		lampName = 'backpanel' + str(self.state)
		if on:
			self.game.lamps[lampName].pulse(0)
		else:
			self.game.lamps[lampName].disable()

	def targetHit(self,sw):
		self.update_lamps(0)
		if (self.state == 7):
			self.state = 1
		else:
			self.state += 1
		self.update_lamps(1)
		self.game.score(1000)
	
	def sw_leftRampEnter_closed(self, sw):
		self.game.coils.plunderDiskMotor.pulse(0)
		self.game.coils.plunderPin.pulse(0)
		# Cancel first just in case the delay functions were already set up.
		self.cancel_delayed(name='plunder_falsestart')
		self.cancel_delayed(name='plunder_complete')
		self.delay(name='plunder_falsestart', event_type=None, delay=2.0, handler=self.plunder_stop)
		self.delay(name='plunder_complete', event_type=None, delay=7.0, handler=self.plunder_stop)

	def sw_plunderEnter_open(self, sw):
		self.cancel_delayed(name='plunder_falsestart')
	
	def plunder_stop(self):
		self.game.coils.plunderDiskMotor.disable()
		self.game.coils.plunderPin.disable()
	
class ExitMode(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ExitMode, self).__init__(game, priority)
		self.delay(name='keyboard_events', event_type=None, delay=.250, handler=self.keyboard_events)
		self.ctrl = 0

	def keyboard_events(self):
		self.delay(name='keyboard_events', event_type=None, delay=.250, handler=self.keyboard_events)
		for event in pygame.event.get():
			print "hi"
			if event.type == KEYDOWN:
				if event.key == K_RCTRL or event.key == K_LCTRL:
					self.ctrl = 1
				if event.key == K_c:
					if self.ctrl == 1:
						self.game.end_run_loop()
				if (event.key == K_ESCAPE):
					self.game.end_run_loop()
			if event.type == KEYUP:
				if event.key == K_RCTRL or event.key == K_LCTRL:
					self.ctrl = 0
		

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

class PopupDisplay(game.Mode):
	"""Displays a pop-up message on the DMD."""
	def __init__(self, game):
		super(PopupDisplay, self).__init__(game, 0)
		self.__status_layer = dmd.TextLayer(128/2, 32-2*7, font_tiny7, "center")
	
	def set_text(self, text, seconds=3):
		self.__status_layer.set_text(text, seconds)
	
	def mode_started(self):
		self.game.dmd.layers.insert(0, self.__status_layer)
		
	def mode_stopped(self):
		self.game.dmd.layers.remove(self.__status_layer)

def commatize(n):
	return locale.format("%d", n, True)
	
print("Initializing sound...")
from pygame import mixer # This call takes a while.

class SoundController(object):
	"""docstring for TestGame"""
	def __init__(self, delegate):
		super(SoundController, self).__init__()
		mixer.init()
		self.sounds = {}
		self.music = {}
		self.set_volume(0.5)
                                             
                #self.register_music('wizard',"sound/pinball_wizard.mp3")
		#self.play_music('wizard')

	def play_music(self, key):
		self.load_music(key)
		mixer.music.play()

	def stop_music(self, key):
		mixer.music.stop()

	def load_music(self, key):
		mixer.music.load(self.music[key])

	def register_sound(self, key, sound_file):
		self.new_sound = mixer.Sound(str(sound_file))
                self.sounds[key] = self.new_sound
		self.sounds[key].set_volume(self.volume)

	def register_music(self, key, music_file):
                self.music[key] = music_file

	def play(self,key):
		self.sounds[key].play()

	def volume_up(self):
		if (self.volume < 0.8):
			self.set_volume(self.volume + 0.1)
		return self.volume*10

	def volume_down(self):
		if (self.volume > 0.2):
			self.set_volume(self.volume - 0.1)
		return self.volume*10

	def set_volume(self, new_volume):
		self.volume = new_volume
		mixer.music.set_volume (new_volume)
		for key in self.sounds:
			self.sounds[key].set_volume(self.volume)

	def beep(self):
		pass
	#	self.play('chime')

	#def play(self, name):
	#	self.chuck.add_shred('sound/'+name)
	#	self.chuck.poll()
	#	pass
	#def on_add_shred(self, num, name):
	#	pass
	#def on_rm_shred(self, num, name):
	#	pass

class TestGame(game.GameController):
	"""docstring for TestGame"""
	def __init__(self, machineType):
		super(TestGame, self).__init__(machineType)
		self.sound = SoundController(self)
		self.dmd = dmd.DisplayController(self.proc, width=128, height=32)
		self.popup = PopupDisplay(self)
		self.exit_mode = ExitMode(self, 1)
		self.modes.add(self.exit_mode)
		
	def setup(self):
		"""docstring for setup"""
		self.load_config(config_path)
		print("Initial switch states:")
		for sw in self.switches:
			print("  %s:\t%s" % (sw.name, sw.state_str()))

                self.setup_ball_search()

		self.start_of_ball_mode = StartOfBall(self)
		self.attract_mode = Attract(self)

                self.sound.register_sound('service_enter', sound_path+"menu_in.wav")
                self.sound.register_sound('service_exit', sound_path+"menu_out.wav")
                self.sound.register_sound('service_next', sound_path+"next_item.wav")
                self.sound.register_sound('service_previous', sound_path+"previous_item.wav")
                self.sound.register_sound('service_switch_edge', sound_path+"switch_edge.wav")
		self.service_mode = procgame.service.ServiceMode(self,100,font_tiny7)
		self.reset()
		
	def reset(self):
		super(TestGame, self).reset()
		self.modes.add(self.popup)
		self.modes.add(self.attract_mode)
	        self.modes.add(self.ball_search)
		
	def ball_starting(self):
		super(TestGame, self).ball_starting()
		self.modes.add(self.start_of_ball_mode)
		
	def ball_ended(self):
		self.modes.remove(self.start_of_ball_mode)
		super(TestGame, self).ball_ended()
		
	def game_ended(self):
		super(TestGame, self).game_ended()
		self.modes.remove(self.start_of_ball_mode)
		self.modes.add(self.attract_mode)
		# for mode in copy.copy(self.modes.modes):
		# 	self.modes.remove(mode)
		# self.reset()
		self.set_status("Game Over")

	def dmd_event(self):
		"""Called by the GameController when a DMD event has been received."""
		self.dmd.update()
		
	def is_ball_in_play(self):
		return self.switches.trough4.is_open() # TODO: Check other trough switches.
	
	def set_status(self, text):
		self.popup.set_text(text)
		print(text)
	
	def score(self, points):
		p = self.current_player()
		p.score += points

	def setup_ball_search(self):
		special_handler_modes = []
		# Give ball search priority of 100.
		# It should always be the highest priority so nothing can keep
		# switch events from getting to it.
		self.ball_search = procgame.ballsearch.BallSearch(self, priority=100, countdown_time=10, coils=self.ballsearch_coils, reset_switches=self.ballsearch_resetSwitches, stop_switches=self.ballsearch_stopSwitches,special_handler_modes=special_handler_modes)

def main():
	machineType = 'sternSAM'
	game = None
	try:
	 	game = TestGame(machineType)
		game.setup()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()
