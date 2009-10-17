import procgame
import pinproc
from deadworld import *
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
pygame.display.set_caption('JDTEST - Press CTRL-C to exit')
#font = pygame.font.Font('./freesansbold.ttf', 17)
#text = font.render('Press ESC to exit', True, (15, 255, 105))
#pygame.mouse.set_visible(0)
# Create a rectangle
#textRect = text.get_rect()

# Center the rectangle
#textRect.centerx = screen.get_rect().centerx
#textRect.centery = screen.get_rect().centery
# Blit the text
#screen.blit(text, textRect)


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
		press_start = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("Press Start")
		proc_banner = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("pyprocgame")
		splash = dmd.FrameLayer(opaque=True, frame=dmd.Animation().load(fonts_path+'Splash.dmd').frames[0])
		self.layer = dmd.ScriptedLayer(128, 32, [{'seconds':2.0, 'layer':splash}, {'seconds':2.0, 'layer':press_start}, {'seconds':2.0, 'layer':proc_banner}, {'seconds':2.0, 'layer':None}])
		self.layer.opaque = True

	def mode_topmost(self):
		self.game.lamps.startButton.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
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
			self.game.deadworld.perform_ball_search()
		return True


class StartOfBall(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(StartOfBall, self).__init__(game, 2)
		self.ball_save = procgame.ballsave.BallSave(self.game, self.game.lamps.drainShield)
		self.tilt_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("TILT!")
		self.layer = dmd.GroupedLayer(128, 32, [self.tilt_layer])

	def mode_started(self):
		self.game.coils.flasherPursuitL.schedule(0x00001010, cycle_seconds=1, now=False)
		self.game.coils.flasherPursuitR.schedule(0x00000101, cycle_seconds=1, now=False)
		self.game.enable_flippers(enable=True)
		self.game.lamps.gi02.pulse(0)
		self.game.lamps.gi03.pulse(0)
		self.game.lamps.startButton.disable()
		self.game.coils.trough.pulse(20)
			
		#else: 
			#self.game.set_status("Ball Search!")
		#	search = procgame.modes.BallSearch(self.game, priority=8)
		#        self.game.modes.add(search)
		#	search.perform_search()
			#search.pop_coil()
		self.drops = procgame.modes.BasicDropTargetBank(self.game, priority=8, prefix='dropTarget', letters='JUDGE')
		self.multiball = Multiball(self.game, 8, self.game.deadworld_mod_installed)
		#self.drops = procgame.modes.ProgressiveDropTargetBank(self.game, priority=8, prefix='dropTarget', letters='JUDGE', advance_switch='subwayEnter1')
		self.drops.on_advance = self.on_drops_advance
		self.drops.on_completed = self.on_drops_completed
		self.drops.auto_reset = False
		self.game.modes.add(self.drops)
		self.game.modes.add(self.multiball)
		self.multiball.update_info_record(self.game.get_player_record('MB'))
		self.drop_targets_completed_hurryup = DropTargetsCompletedHurryup(self.game, priority=self.priority+1, drop_target_mode=self.drops)
		self.auto_plunge = 0
		self.game.modes.add(self.ball_save)
		self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=1, time=12, now=False, allow_multiple_saves=False)
		self.game.ball_search.enable()
		self.times_warned = 0;
		self.tilt_status = 0

	
	def mode_stopped(self):
		self.game.enable_flippers(enable=False)
		self.game.modes.remove(self.drops)
		self.game.modes.remove(self.multiball)
		self.game.modes.remove(self.drop_targets_completed_hurryup) # TODO: Should track parent/child relationship for modes and remove children when parent goes away..?
		self.game.modes.remove(self.ball_save)
		self.game.ball_search.disable()
	
	def sw_slingL_closed(self, sw):
		self.game.score(100)
	def sw_slingR_closed(self, sw):
		self.game.score(100)

	# Test of is_active()
	#def sw_threeBankTargets_closed(self, sw):
	#	if self.game.switches.shooterR.is_active():
	#		self.game.score(100)
	
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
		self.trough_check();

	def sw_trough2_open_for_500ms(self, sw):
		self.trough_check();

	def sw_trough3_open_for_500ms(self, sw):
		self.trough_check();

	def sw_trough4_open_for_500ms(self, sw):
		self.trough_check();

	def sw_trough5_open_for_500ms(self, sw):
		self.trough_check();
		
	def trough_check(self):
		if (self.ball_save.is_active()):
			num_balls_out = self.game.deadworld.get_num_balls_locked() + (self.ball_save.num_balls_to_save - 1)
			print "checking is trough full"
			print self.game.deadworld.num_balls_locked
			print self.ball_save.num_balls_to_save
			print self.game.num_balls_total-num_balls_out
			if self.game.is_trough_full(self.game.num_balls_total-num_balls_out):
				self.ball_save.saving_ball()
				self.game.coils.trough.pulse(20)	
				self.game.set_status("Ball Saved!")
		else:
			#in_play = self.game.is_ball_in_play()
			if self.multiball.is_active():
				if self.game.is_trough_full(self.game.num_balls_total-(self.game.deadworld.get_num_balls_locked()+1)):
					self.multiball.end_multiball()
			elif self.game.is_trough_full(self.game.num_balls_total-self.game.deadworld.get_num_balls_locked()):
				if self.tilt_status:
					self.game.dmd.layers.remove(self.layer)
				mb_info_record = self.multiball.get_info_record()
				self.game.update_player_record('MB', mb_info_record)
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

	# Test code for active/inactive
	#def sw_shooterR_active_for_1s(self,sw):
	#	self.game.set_status('Yippee')

	#def sw_shooterR_inactive_for_3s(self,sw):
	#	self.game.set_status('Double Yippee')

	def sw_shooterR_open_for_2s(self,sw):
		self.auto_plunge = 1

	def sw_shooterR_closed_for_300ms(self,sw):
		if (self.auto_plunge):
			self.game.coils.shooterR.pulse(50)

	def sw_tilt_active(self, sw):
		if self.times_warned == 2:
			self.tilt()
		else:
			self.times_warned += 1
			#play sound
			#add a display layer and add a delayed removal of it.
			self.game.set_status("Warning " + str(self.times_warned) + "!")

	def tilt(self):
		if self.tilt_status == 0:
			self.game.dmd.layers.append(self.layer)
			self.game.modes.remove(self.drops)
			self.game.modes.remove(self.drop_targets_completed_hurryup)
			self.ball_save.disable()
			self.game.modes.remove(self.ball_save)
			self.game.ball_search.disable()
			self.game.enable_flippers(enable=False)
			for lamp in self.game.lamps:
				lamp.disable()
			if self.game.switches.shooterR.is_active():
				self.game.coils.shooterR.pulse(50)
			if self.game.switches.shooterL.is_active():
				self.game.coils.shooterL.pulse(20)
			self.tilt_status = 1
			#play sound
			#play video


	def flash_then_pop(self, flasher, coil, pulse):
		self.game.coils[flasher].schedule(0x00555555, cycle_seconds=1, now=True)
		self.delay(name='delayed_pop', event_type=None, delay=1.0, handler=self.delayed_pop, param=[coil, pulse])

	def delayed_pop(self, coil_pulse):
		self.game.coils[coil_pulse[0]].pulse(coil_pulse[1])	


class Multiball(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, deadworld_mod_installed):
		super(Multiball, self).__init__(game, priority)
		self.deadworld_mod_installed = deadworld_mod_installed
		self.lock_enabled = 0
		self.num_balls_locked = 0
		self.num_balls_to_eject = 0
		self.num_left_ramp_shots = 0
		self.virtual_locks_needed = 0
		self.banner_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
		self.state = 'load'
		self.displaying_text = 0
		self.enable_ball_save_after_launch=False
	
	def mode_started(self):
		self.game.coils.globeMotor.disable()
		self.lock_lamps()
		self.game.deadworld.initialize()
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 250, True, False)

	def mode_stopped(self):
		self.game.coils.flasherGlobe.disable()
		self.game.lamps.gi04.disable()
		#if self.displaying_text:
		#	self.game.dmd.layers.remove(self.layer)
		#	self.cancel_delayed(['remove_dmd_layer'])

	def is_active(self):
		return self.state == 'multiball'

	def end_multiball(self):
		self.state = 'multiball_complete'
		self.game.set_status(self.state)
		self.game.lamps.gi04.disable()

	def display_text(self, text):
		# use a varable to protect against adding the layer twice
		#if self.displaying_text:
		#	self.game.dmd.layers.remove(self.layer)
		#	self.cancel_delayed(['remove_dmd_layer'])
		#self.displaying_text = 1
		self.banner_layer.set_text(text,3)
		self.game.dmd.layers.append(self.layer)
		self.delay(name='remove_dmd_layer', event_type=None, delay=2.5, handler=self.remove_dmd_layer)

	def remove_dmd_layer(self):
		self.game.dmd.layers.remove(self.layer)
		self.displaying_text = 0

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.state = info_record[0]
			self.num_balls_locked = info_record[1]

		# Virtual locks are needed when there are more balls physically locked 
		# than the player has locked through play.  This happens when
		# another player locks more balls than the current player.  Use
		# Virtual locks > 0 for this case.
		# Use Virtual locks < 0 when the player has locked more balls than are
		# physically locked.  This could happen when another player plays
		# multiball and empties the locked balls.
		if self.deadworld_mod_installed:
			self.virtual_locks_needed = self.game.deadworld.num_balls_locked - self.num_balls_locked

		if self.virtual_locks_needed < 0:
			# enable the lock the player can quickly re-lock
			self.enable_lock()
			self.num_balls_locked = self.game.deadworld.num_balls_locked
			# pre-set the ramp shots to get the lock light blinking appropriately
			self.num_left_ramp_shots = 3
		self.lock_lamps()

	def get_info_record(self):
		info_record = [self.state, self.num_balls_locked]
		return info_record

	def disable_lock(self):
		self.game.deadworld.disable_lock()
		self.lock_enabled = 0
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 250, True, False)

	def enable_lock(self):
		self.display_text("Lock is Lit!")
		self.game.deadworld.enable_lock()
		self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)
		self.lock_enabled = 1
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 250, True, True)
		

	def sw_leftRampToLock_active(self, sw):
		if self.lock_enabled:
			self.game.coils.flasherGlobe.schedule(schedule=0xAAAAAAAA, cycle_seconds=2, now=True)
			self.num_balls_locked += 1
			self.display_text("Ball " + str(self.num_balls_locked) + " Locked!")
			# Player needs to re-fill the locks
			if self.virtual_locks_needed < 0:
				# Increment back towards 0
				self.virtual_locks_needed += 1
				# Launch a new ball since the current one is locked.
				self.launch_ball(1)
				# See if finished re-locking
				if self.virtual_locks_needed == 0:
					self.disable_lock()
			else:	
				# Start multiball with the 4th lock
				if self.num_balls_locked == 4:
					if self.deadworld_mod_installed:
						self.game.deadworld.eject_balls(4)
						self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=4, time=25, now=True, allow_multiple_saves=True)
					else:
						self.launch_ball(3)
						self.enable_ball_save_after_launch=True
						self.delay(name='stop_globe', event_type=None, delay=7.0, handler=self.stop_globe)
					self.num_balls_locked = 0
					self.state = 'multiball'
					self.game.lamps.gi04.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
					self.display_text("Multiball!")
				# When not yet multiball, launch a new ball each time
				# one is locked.
				elif self.deadworld_mod_installed:
					self.launch_ball(1)
				self.disable_lock()	
				# Reset the ramp count
				self.num_left_ramp_shots = 0
		else:
			if self.deadworld_mod_installed:
				self.game.deadworld.eject_balls(1)
		self.lock_lamps()

	def sw_leftRampExit_active(self,sw):
		#ignore slow moving balls that made it by the diverter
		if self.state == 'load':
			if not self.lock_enabled:
				# Prepare to lock
				if self.num_left_ramp_shots == 2:
					# Don't enable locks if doing virtual locks.
					if self.virtual_locks_needed == 0:
						self.enable_lock()
					self.num_left_ramp_shots += 1

				# Should only get here if doing virtual locks,
				# but check anyway.
				elif self.num_left_ramp_shots == 3:
					if self.virtual_locks_needed > 0:
						self.num_balls_locked += 1
						self.virtual_locks_needed -= 1
						self.num_left_ramp_shots = 0
				else:
					self.num_left_ramp_shots += 1

			self.lock_lamps()

	def lock_lamps(self):
		if self.state == 'load':
			if self.num_left_ramp_shots == 0:
				schedule = 0x0000ffff
			elif self.num_left_ramp_shots == 1:
				schedule = 0x00ff00ff
			elif self.num_left_ramp_shots == 2:
				schedule = 0xf0f0f0f0
			else:
				schedule = 0xaaaaaaaa
			if self.num_balls_locked == 0:
				self.game.lamps.lock1.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock2.disable()
				self.game.lamps.lock3.disable()
			elif self.num_balls_locked == 1:
				self.game.lamps.lock1.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock3.disable()
			elif self.num_balls_locked == 2:
				self.game.lamps.lock1.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock3.schedule(schedule=schedule, cycle_seconds=0, now=True)
			elif self.num_balls_locked == 3:
				self.game.lamps.lock1.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock3.schedule(schedule=schedule, cycle_seconds=0, now=True)
		else:
			self.game.lamps.lock1.disable()
			self.game.lamps.lock2.disable()
			self.game.lamps.lock3.disable()

	def launch_ball(self, num):
		print "Launching Ball"
		self.game.coils.trough.pulse(20)
		num -= 1
		if num > 0:
			self.delay(name='launch', event_type=None, delay=2.0, handler=self.launch_ball, param=num)
		else:
			if self.enable_ball_save_after_launch:
				self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=4, time=25, now=False, allow_multiple_saves=True)
				self.enable_ball_save_after_launch = False
			

	def how_many_balls_locked(self):
		return self.num_balls_locked

	def stop_globe(self):
		self.game.deadworld.mode_stopped()
		
	
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
		#self.add_switch_handler(name='magnetOverRing', event_type='open', delay=None, handler=self.sw_magnetOverRing_open)
		switch_num = self.game.switches['globePosition2'].number
		self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True)

	def mode_started(self):
		self.game.coils.globeMotor.pulse(0)

	def mode_stopped(self):
		self.game.coils.crane.disable()	
		self.game.coils.craneMagnet.disable()
		self.game.coils.globeMotor.disable()

	def sw_globePosition2_closed_for_100ms(self,sw):
		self.game.coils.globeMotor.disable()
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

class ExitMode(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ExitMode, self).__init__(game, priority)
		self.delay(name='keyboard_events', event_type=None, delay=.250, handler=self.keyboard_events)
		self.ctrl = 0

	def keyboard_events(self):
		self.delay(name='keyboard_events', event_type=None, delay=.250, handler=self.keyboard_events)
		for event in pygame.event.get():
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

		self.score_display = scoredisplay.ScoreDisplay(self, 1)
		self.start_of_ball_mode = StartOfBall(self)
		self.attract_mode = Attract(self)
		self.deadworld = Deadworld(self, 20, self.deadworld_mod_installed)

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
		self.modes.add(self.score_display)
		self.modes.add(self.attract_mode)
	        self.modes.add(self.ball_search)
		self.modes.add(self.exit_mode)
		self.modes.add(self.deadworld)
		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)
		
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
		self.deadworld.mode_stopped()
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

	def update_player_record(self, key, record):
		p = self.current_player()
		p.info_record[key] = record

	def get_player_record(self, key):
		p = self.current_player()
		if key in p.info_record:
			return p.info_record[key]
		else:
			return []

	def setup_ball_search(self):
                #deadworld_search = DeadworldReleaseBall(self, priority=99) 
		#special_handler_modes = [deadworld_search]
		special_handler_modes = []
		# Give ball search priority of 100.
		# It should always be the highest priority so nothing can keep
		# switch events from getting to it.
		self.ball_search = procgame.ballsearch.BallSearch(self, priority=100, countdown_time=10, coils=self.ballsearch_coils, reset_switches=self.ballsearch_resetSwitches, stop_switches=self.ballsearch_stopSwitches,special_handler_modes=special_handler_modes)
		
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
