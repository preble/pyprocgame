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

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.

config_path = "../shared/config/JD.yaml"
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
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.disable()

	def mode_started(self):
		#self.game.lamps.startButton.schedule(schedule=0x00000fff, cycle_seconds=0, now=False)
		#self.game.lamps.gi01.pulse(0)
		#self.game.lamps.gi02.disable()
		for name in ['popperL', 'popperR']:
			if self.game.switches[name].is_open():
				self.game.coils[name].pulse()
		for name in ['shooterL', 'shooterR']:
			if self.game.switches[name].is_closed():
				self.game.coils[name].pulse()
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

	def sw_enter_closed(self, sw):
		self.game.modes.add(self.game.service_mode)
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
		if self.game.is_trough_full():
			if self.game.switches.trough6.is_open():
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
                self.ball_save = procgame.ballsave.BallSave(self.game, self.game.lamps.drainShield)

	def mode_started(self):
		self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
		self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)
		self.game.modes.add(self.game_display)
		self.game.enable_flippers(enable=True)
		self.game.lamps.gi02.pulse(0)
		self.game.lamps.gi03.pulse(0)
		self.game.lamps.startButton.disable()
		if self.game.switches.trough6.is_open():
			self.game.coils.trough.pulse(20)
		#else: 
			#self.game.set_status("Ball Search!")
		#	search = procgame.modes.BallSearch(self.game, priority=8)
		#        self.game.modes.add(search)
		#	search.perform_search()
			#search.pop_coil()
		self.drops = procgame.modes.BasicDropTargetBank(self.game, priority=8, prefix='dropTarget', letters='JUDGE')
		#self.drops = procgame.modes.ProgressiveDropTargetBank(self.game, priority=8, prefix='dropTarget', letters='JUDGE', advance_switch='subwayEnter1')
		self.drops.on_advance = self.on_drops_advance
		self.drops.on_completed = self.on_drops_completed
		self.drops.auto_reset = False
		self.game.modes.add(self.drops)
		self.drop_targets_completed_hurryup = DropTargetsCompletedHurryup(self.game, priority=self.priority+1, drop_target_mode=self.drops)
		self.auto_plunge = 0
		self.game.modes.add(self.ball_save)
		self.game.ball_search.enable()

	
	def mode_stopped(self):
		self.game.enable_flippers(enable=False)
		self.game.modes.remove(self.game_display)
		self.game.modes.remove(self.drops)
		self.game.modes.remove(self.drop_targets_completed_hurryup) # TODO: Should track parent/child relationship for modes and remove children when parent goes away..?
		self.game.modes.remove(self.ball_save)
		self.game.ball_search.disable()
	
	def sw_slingL_closed(self, sw):
		self.game.score(100)
	def sw_slingR_closed(self, sw):
		self.game.score(100)
	
	def on_drops_advance(self, mode):
		self.game.sound.beep()
		self.game.score(5000)
		pass
		
	def on_drops_completed(self, mode):
# Here we protect against double-adding this mode because the drops can be a little flaky.
		if self.drop_targets_completed_hurryup not in self.game.modes.modes:
			self.game.sound.beep()
			self.game.score(10000)
			self.game.modes.add(self.drop_targets_completed_hurryup)
	
	def sw_trough1_open_for_500ms(self, sw):
		if (self.ball_save.is_active()):
			self.ball_save.saving_ball()
			self.game.coils.trough.pulse(20)	
		else:
			in_play = self.game.is_ball_in_play()
			if not in_play:
				self.game.end_ball()
				trough6_closed = self.game.switches.trough6.is_open()
				shooterR_closed = self.game.switches.shooterR.is_closed()
				if trough6_closed and not shooterR_closed and self.game.ball != 0:
					self.game.coils.trough.pulse(20)
			# TODO: What if the ball doesn't make it into the shooter lane?
			#       We should check for it on a later mode_tick() and possibly re-pulse.
		return True
	
	def sw_popperL_open(self, sw):
		self.game.set_status("Left popper!")
		
	def sw_popperL_open_for_200ms(self, sw):
		if self.game.disable_popperL != 1:
			self.flash_then_pop('flashersLowerLeft', 'popperL', 50)
			#self.game.coils.flashersLowerLeft.schedule(0x33333, cycle_seconds=1, now=True)

	#def sw_popperL_open_for_500ms(self, sw): # opto!
	#	if self.game.disable_popperL != 1:
	#		self.game.coils.popperL.pulse(50)
	#		self.game.score(2000)

	def sw_popperR_open(self, sw):
		self.game.set_status("Right popper!")

	def sw_popperR_open_for_200ms(self, sw): # opto!
		self.flash_then_pop('flashersRtRamp', 'popperR', 20)
		#self.game.coils.flashersRtRamp.schedule(0x333, cycle_seconds=1, now=True)
		#self.game.coils.popperR.pulse(20)
		#self.game.score(2000)
	
	def sw_rightRampExit_closed(self, sw):
		self.game.set_status("Right ramp!")
		self.game.coils.flashersRtRamp.schedule(0x333, cycle_seconds=1, now=False)
		self.game.score(2000)
	
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
		else:
			self.game.set_status("Hold for 2s to reset.")
	def sw_startButton_closed_for_2s(self, sw):
		if self.game.ball > 1:
			self.game.set_status("Reset!")
			self.game.reset()
			return True
		
	def sw_outlaneL_closed(self, sw):
		self.game.score(1000)
		#self.game.sound.play('outlane')
	def sw_outlaneR_closed(self, sw):
		self.game.score(1000)
		#self.game.sound.play('outlane')

	def sw_enter_closed(self, sw):
		self.game.modes.add(self.game.service_mode)
		return True

	def sw_shooterR_open_for_2s(self,sw):
		self.auto_plunge = 1

	def sw_shooterR_closed_for_2s(self,sw):
		if (self.auto_plunge):
			self.game.coils.shooterR.pulse(50)

	def flash_then_pop(self, flasher, coil, pulse):
		self.game.coils[flasher].schedule(0x00555555, cycle_seconds=1, now=True)
		self.delay(name='delayed_pop', event_type=None, delay=1.0, handler=self.delayed_pop, param=[coil, pulse])

	def delayed_pop(self, coil_pulse):
		self.game.coils[coil_pulse[0]].pulse(coil_pulse[1])	



class DropTargetsCompletedHurryup(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, drop_target_mode):
		super(DropTargetsCompletedHurryup, self).__init__(game, priority)
		self.drop_target_mode = drop_target_mode
		self.countdown_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center")
		self.banner_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.countdown_layer, self.banner_layer])
	
	def mode_started(self):
		self.game.dmd.layers.append(self.layer)
		self.banner_layer.set_text("HURRY-UP!", 3)
		self.seconds_remaining = 13
		self.update_and_delay()
		self.game.lamps.multiballJackpot.schedule(schedule=0x33333333, cycle_seconds=0, now=True)

	def mode_stopped(self):
		self.game.dmd.layers.remove(self.layer)
		self.drop_target_mode.animated_reset(1.0)
		self.game.lamps.multiballJackpot.disable()
		self.game.disable_popperL = 0
		if self.game.switches.popperL.is_open():
			self.game.coils.popperL.pulse(40)
	
	def sw_subwayEnter1_closed(self, sw):
		self.game.score(1000*1000)
		# Set award message.  Keep it on the DMD long enough to reset the mode (to avoid seeing the countdown layer now that it's irrelevant.
		self.banner_layer.set_text("1 MILLION!", 5)
		self.game.coils.flasherGlobe.pulse(50)
		self.cancel_delayed(['grace', 'countdown'])
		self.delay(name='end_of_mode', event_type=None, delay=3.0, handler=self.delayed_removal)
		#Don't allow the popper to kick the ball back out until the mode is reset.
		self.game.disable_popperL = 1
	
	def update_and_delay(self):
		self.countdown_layer.set_text("%d seconds" % (self.seconds_remaining))
		self.delay(name='countdown', event_type=None, delay=1, handler=self.one_less_second)
		
	def one_less_second(self):
		self.seconds_remaining -= 1
		if self.seconds_remaining >= 0:
			self.update_and_delay()
		else:
			self.delay(name='grace', event_type=None, delay=0.5, handler=self.delayed_removal)
			
	def delayed_removal(self):
		self.game.modes.remove(self)
		
class DeadworldReleaseBall(game.Mode):
	"""Deadworld Mode."""
	def __init__(self, game, priority):
		super(DeadworldReleaseBall, self).__init__(game, priority)
		#self.add_switch_handler(name='globePosition2', event_type='open', delay=None, handler=self.sw_globePosition2_closed)
		self.add_switch_handler(name='magnetOverRing', event_type='open', delay=None, handler=self.sw_magnetOverRing_open)
		switch_num = self.game.switches['globePosition2'].number
		self.game.install_switch_rule(switch_num, 'closed_debounced', 'globeMotor', True)

	def mode_started(self):
		self.game.coils.globeMotor.pulse(0)

	def mode_stopped(self):
		self.game.coils.crane.disable()	
		self.game.coils.craneMagnet.disable()
		self.game.coils.globeMotor.disable()

	def sw_globePosition2_closed_for_100ms(self,sw):
		#self.game.coils.globeMotor.disable()
		self.game.coils.crane.pulse(0)

	def sw_magnetOverRing_open(self,sw):
		self.game.coils.craneMagnet.pulse(0)
		self.delay(name='crane_release', event_type=None, delay=2, handler=self.crane_release)

	def crane_release(self):
		self.game.coils.crane.disable()
		self.game.coils.craneMagnet.disable()
	
	def sw_startButton_closed(self,sw):
		# Ignore start button while this mode is active
		return True


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
	
	def mode_tick(self):
		#if len(self.game.modes.modes) > 0:
		#	self.mode_layer.set_text('Topmost: '+str(self.game.modes.modes[0].status_str()))
		self.game.dmd.update()

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
		self.disable_popperL = 0
		
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
		
	def is_ball_in_play(self):
		return self.switches.trough1.is_closed() # TODO: Check other trough switches.
	
	def set_status(self, text):
		self.popup.set_text(text)
		print(text)
	
	def score(self, points):
		p = self.current_player()
		p.score += points

	def setup_ball_search(self):
		# Set up ball search.  These hardcoded lists should be set up automatically.  The changes to do that depend on to-be-implemented YAML settings which allow switches and coils for the ball search to be identified in the YAML file.
		search_coils = [self.coils.popperR, \
                                self.coils.popperL, \
                                self.coils.shooterL, \
                                self.coils.shooterR, \
                                self.coils.slingL, \
                                self.coils.slingR, \
                                self.coils.resetDropTarget]
		search_switches = ["shooterR", "shooterL", \
                                   "flipperLwL", "flipperLwR", \
                                   "inlaneR", "inlaneL", \
                                   "subwayEnter1", "subwayEnter2", \
                                   "outlaneR", "outlaneL", \
                                   "inlaneFarR", \
                                   "slingR", "slingL", \
                                   "captiveBall2", \
                                   "dropTargetJ", "dropTargetU", "dropTargetD", \
                                   "dropTargetG", "dropTargetE", \
                                   "popperR", "popperL", \
                                   "rightRampExit"] 
		stop_switches = ["shooterR", "shooterL", \
                                 "flipperLwL", "flipperLwR",
                                 "startButton" ]
                deadworld_search = DeadworldReleaseBall(self, priority=99) 
		special_handler_modes = [deadworld_search]
		# Give ball search priority of 100.
		# It should always be the highest priority so nothing can keep
		# switch events from getting to it.
		self.ball_search = procgame.ballsearch.BallSearch(self, priority=100, countdown_time=10, reset_switch_names=search_switches, disable_switch_names=stop_switches,coils=search_coils,special_handler_modes=special_handler_modes)
		
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
