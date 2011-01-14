# Setup logging first thing in case any of the modules log something as they start:
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

import sys
sys.path.append(sys.path[0]+'/../..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame
import pinproc
from procgame import *
from threading import Thread
from random import *
import string
import time
import locale
import math
import copy
import yaml

locale.setlocale(locale.LC_ALL, "") # Used to put commas in the score.


dmd_path = "../shared/dmd/"
sound_path = "../shared/sound/"
font_tiny7 = dmd.font_named("04B-03-7px.dmd")
font_jazz18 = dmd.font_named("Jazz18-18px.dmd")

class Attract(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(Attract, self).__init__(game, 1)
		self.press_start = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("Press Start")
		self.proc_banner = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("pyprocgame")
		self.game_title = dmd.TextLayer(128/2, 7, font_jazz18, "center", opaque=True).set_text("Starter")
		self.splash = dmd.FrameLayer(opaque=True, frame=dmd.Animation().load(dmd_path+'Splash.dmd').frames[0])
		self.layer = dmd.ScriptedLayer(128, 32, [{'seconds':2.0, 'layer':self.splash}, {'seconds':2.0, 'layer':self.proc_banner}, {'seconds':2.0, 'layer':self.game_title}, {'seconds':2.0, 'layer':self.press_start}, {'seconds':2.0, 'layer':None}])

	def mode_topmost(self):
		pass

	def mode_started(self):
		# Blink the start button to notify player about starting a game.
		self.game.lamps.startButton.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=False)
		# Turn on minimal GI lamps
		# Some games don't have controllable GI's (ie Stern games)
		#self.game.lamps.gi01.pulse(0)
		#self.game.lamps.gi02.disable()


	def mode_stopped(self):
		pass
		
	def mode_tick(self):
		pass

	# Enter service mode when the enter button is pushed.
	def sw_enter_active(self, sw):
		for lamp in self.game.lamps:
			lamp.disable()
		self.game.modes.add(self.game.service_mode)
		return True

	def sw_exit_active(self, sw):
		return True

	# Outside of the service mode, up/down control audio volume.
	def sw_down_active(self, sw):
		volume = self.game.sound.volume_down()
		self.game.set_status("Volume Down : " + str(volume))
		return True

	def sw_up_active(self, sw):
		volume = self.game.sound.volume_up()
		self.game.set_status("Volume Up : " + str(volume))
		return True

	# Start button starts a game if the trough is full.  Otherwise it
	# initiates a ball search.
	# This is probably a good place to add logic to detect completely lost balls.
	# Perhaps if the trough isn't full after a few ball search attempts, it logs a ball
	# as lost?	
	def sw_startButton_active(self, sw):
		if self.game.trough.is_full:
			# Remove attract mode from mode queue - Necessary?
			self.game.modes.remove(self)
			# Initialize game	
			self.game.start_game()
			# Add the first player
			self.game.add_player()
			# Start the ball.  This includes ejecting a ball from the trough.
			self.game.start_ball()
		else: 
			
			self.game.set_status("Ball Search!")
			self.game.ball_search.perform_search(5)
		return True


class BaseGameMode(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(BaseGameMode, self).__init__(game, 2)
		self.tilt_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("TILT!")
		self.layer = None # Presently used for tilt layer
		self.ball_starting = True

	def mode_started(self):

		# Disable any previously active lamp
		for lamp in self.game.lamps:
			lamp.disable()

		# Turn on the GIs
		# Some games don't have controllable GI's (ie Stern games)
		#self.game.lamps.gi01.pulse(0)
		#self.game.lamps.gi02.pulse(0)
		#self.game.lamps.gi03.pulse(0)
		#self.game.lamps.gi04.pulse(0)

		# Enable the flippers
		self.game.enable_flippers(enable=True)

		# Put the ball into play and start tracking it.
		# self.game.coils.trough.pulse(40)
		self.game.trough.launch_balls(1, self.ball_launch_callback)

		# Enable ball search in case a ball gets stuck during gameplay.
		self.game.ball_search.enable()

		# Reset tilt warnings and status
		self.times_warned = 0;
		self.tilt_status = 0

		# In case a higher priority mode doesn't install it's own ball_drained
		# handler.
		self.game.trough.drain_callback = self.ball_drained_callback

		# Each time this mode is added to game Q, set this flag true.
		self.ball_starting = True

	def ball_launch_callback(self):
		if self.ball_starting:
			self.game.ball_save.start_lamp()
	
	def mode_stopped(self):
		
		# Ensure flippers are disabled
		self.game.enable_flippers(enable=False)

		# Deactivate the ball search logic so it won't search due to no 
		# switches being hit.
		self.game.ball_search.disable()

	def ball_drained_callback(self):
		if self.game.trough.num_balls_in_play == 0:
			# End the ball
			self.finish_ball()


	def finish_ball(self):

		# Turn off tilt display (if it was on) now that the ball has drained.
		if self.tilt_status and self.layer == self.tilt_layer:
			self.layer = None

		self.end_ball()

	def end_ball(self):
		# Tell the game object it can process the end of ball
		# (to end player's turn or shoot again)
		self.game.end_ball()

	def sw_startButton_active(self, sw):
		if self.game.ball == 1:
			p = self.game.add_player()
			self.game.set_status(p.name + " added!")

	def sw_shooterR_open_for_1s(self,sw):
		if self.ball_starting:
			self.ball_starting = False
			ball_save_time = 10
			self.game.ball_save.start(num_balls_to_save=1, time=ball_save_time, now=True, allow_multiple_saves=False)
		#else:
		#	self.game.ball_save.disable()

	# Note: Game specific item
	# Set the switch name to the launch button on your game.
	# If manual plunger, remove the whole section.
	def sw_fireR_active(self, sw):
		if self.game.switches.shooterR.is_active():
			self.game.coils.shooterR.pulse(50)
		

	# Allow service mode to be entered during a game.
	def sw_enter_active(self, sw):
		self.game.modes.add(self.game.service_mode)
		return True

	def sw_tilt_active(self, sw):
		if self.times_warned == 2:
			self.tilt()
		else:
			self.times_warned += 1
			#play sound
			#add a display layer and add a delayed removal of it.
			self.game.set_status("Tilt Warning " + str(self.times_warned) + "!")

	def tilt(self):
		# Process tilt.
		# First check to make sure tilt hasn't already been processed once.
		# No need to do this stuff again if for some reason tilt already occurred.
		if self.tilt_status == 0:
			
			# Display the tilt graphic
			self.layer = self.tilt_layer

			# Disable flippers so the ball will drain.
			self.game.enable_flippers(enable=False)

			# Make sure ball won't be saved when it drains.
			self.game.ball_save.disable()
			#self.game.modes.remove(self.ball_save)

			# Make sure the ball search won't run while ball is draining.
			self.game.ball_search.disable()

			# Ensure all lamps are off.
			for lamp in self.game.lamps:
				lamp.disable()

			# Kick balls out of places it could be stuck.
			if self.game.switches.shooterR.is_active():
				self.game.coils.shooterR.pulse(50)
			if self.game.switches.shooterL.is_active():
				self.game.coils.shooterL.pulse(20)
			self.tilt_status = 1
			#play sound
			#play video



class Game(game.BasicGame):
	"""docstring for Game"""
	def __init__(self, machine_type):
		super(Game, self).__init__(machine_type)
		self.sound = procgame.sound.SoundController(self)
		self.lampctrl = procgame.lamps.LampController(self)
		self.settings = {}

	def save_settings(self):
		#self.write_settings(user_settings_path)
		pass
		
	def setup(self):
		"""docstring for setup"""
		self.load_config(self.yamlpath)
		#self.load_settings(settings_path, user_settings_path)

		self.setup_ball_search()

		# Instantiate basic game features
		self.attract_mode = Attract(self)
		self.base_game_mode = BaseGameMode(self)
		# Note - Game specific item:
		# The last parameter should be the name of the game's ball save lamp
		self.ball_save = procgame.modes.BallSave(self, self.lamps.drainShield, 'shooterR')

		trough_switchnames = []
		# Note - Game specific item:
		# This range should include the number of trough switches for 
		# the specific game being run.  In range(1,x), x = last number + 1.
		for i in range(1,7):
			trough_switchnames.append('trough' + str(i))
		early_save_switchnames = ['outlaneR', 'outlaneL']

		# Note - Game specific item:
		# Here, trough6 is used for the 'eject_switchname'.  This must
		# be the switch of the next ball to be ejected.  Some games
		# number the trough switches in the opposite order; so trough1
		# might be the proper switchname to user here.
		self.trough = procgame.modes.Trough(self,trough_switchnames,'trough6','trough', early_save_switchnames, 'shooterR', self.drain_callback)
	
		# Link ball_save to trough
		self.trough.ball_save_callback = self.ball_save.launch_callback
		self.trough.num_balls_to_save = self.ball_save.get_num_balls_to_save
		self.ball_save.trough_enable_ball_save = self.trough.enable_ball_save

		# Setup and instantiate service mode
		self.sound.register_sound('service_enter', sound_path+"menu_in.wav")
		self.sound.register_sound('service_exit', sound_path+"menu_out.wav")
		self.sound.register_sound('service_next', sound_path+"next_item.wav")
		self.sound.register_sound('service_previous', sound_path+"previous_item.wav")
		self.sound.register_sound('service_switch_edge', sound_path+"switch_edge.wav")
		self.sound.register_sound('service_save', sound_path+"save.wav")
		self.sound.register_sound('service_cancel', sound_path+"cancel.wav")
		self.service_mode = procgame.service.ServiceMode(self,100,font_tiny7,[])

		# Setup fonts
		self.fonts = {}
		self.fonts['tiny7'] = font_tiny7
		self.fonts['jazz18'] = font_jazz18

		# Instead of resetting everything here as well as when a user
		# initiated reset occurs, do everything in self.reset() and call it
		# now and during a user initiated reset.
		self.reset()

	def reset(self):
		# Reset the entire game framework
		super(Game, self).reset()

		# Add the basic modes to the mode queue
		self.modes.add(self.attract_mode)
		self.modes.add(self.ball_search)
		self.modes.add(self.ball_save)
		self.modes.add(self.trough)

		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)

	# Empty callback just incase a ball drains into the trough before another
	# drain_callback can be installed by a gameplay mode.
	def drain_callback(self):
		pass
		
	def ball_starting(self):
		super(Game, self).ball_starting()
		self.modes.add(self.base_game_mode)
		
	def ball_ended(self):
		self.modes.remove(self.base_game_mode)
		super(Game, self).ball_ended()
		
	def game_ended(self):
		super(Game, self).game_ended()
		self.modes.remove(self.base_game_mode)
		self.set_status("Game Over")
		self.modes.add(self.attract_mode)
		
	def set_status(self, text):
		self.dmd.set_message(text, 3)
		print(text)
	
	def extra_ball(self):
		p = self.current_player()
		p.extra_balls += 1

	def setup_ball_search(self):
		# No special handlers in starter game.
		special_handler_modes = []
		self.ball_search = procgame.modes.BallSearch(self, priority=100, \
                                     countdown_time=10, coils=self.ballsearch_coils, \
                                     reset_switches=self.ballsearch_resetSwitches, \
                                     stop_switches=self.ballsearch_stopSwitches, \
                                     special_handler_modes=special_handler_modes)
		
def main():
	if len(sys.argv) < 2:
		print("Usage: %s <yaml>"%(sys.argv[0]))
		return
	else:
		yamlpath = sys.argv[1]
		if yamlpath.find('.yaml', 0) == -1:
			print("Usage: %s <yaml>"%(sys.argv[0]))
			return

	config = yaml.load(open(yamlpath, 'r'))
	machine_type = config['PRGame']['machineType']
	config = 0
	game = None
	try:
	 	game = Game(machine_type)
		game.yamlpath = yamlpath
		game.setup()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()
