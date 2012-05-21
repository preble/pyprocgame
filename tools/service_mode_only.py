import sys
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
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

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

fonts_path = "../shared/dmd/"
sound_path = "../shared/sound/"
font_tiny7 = dmd.Font(fonts_path+"04B-03-7px.dmd")
font_jazz18 = dmd.Font(fonts_path+"Jazz18-18px.dmd")

class Attract(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		super(Attract, self).__init__(game, 1)
		self.press_start = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("Press Enter")
		self.proc_banner = dmd.TextLayer(128/2, 7, font_jazz18, "center").set_text("pyprocgame")
		self.splash = dmd.FrameLayer(opaque=True, frame=dmd.Animation().load(fonts_path+'Splash.dmd').frames[0])
		self.layer = dmd.ScriptedLayer(128, 32, [{'seconds':2.0, 'layer':self.splash}, {'seconds':2.0, 'layer':self.press_start}, {'seconds':2.0, 'layer':self.proc_banner} ])
		self.layer.opaque = True

	def mode_topmost(self):
		pass

	def mode_started(self):
		# Only mess with gi if the machine has gi's configured.  Stern machines don't have
		# user controllable GI circuits


		for lamp in self.game.lamps:
			if lamp.name.find('gi0', 0) != -1:
				lamp.pulse(0)

		lamp_schedules = []
		for i in range(0,32):
			lamp_schedules.append(0xffff0000 >> i)
			if i > 16:
				lamp_schedules[i] = (lamp_schedules[i] | (0xffff << (32-(i-16)))) & 0xffffffff
			#print("schedule %08x" % (lamp_schedules[i]))

		shuffle(lamp_schedules)
		i = 0
		for lamp in self.game.lamps:
			if lamp.name.find('gi0', 0) == -1 and \
                           lamp.name != 'startButton' and lamp.name != 'buyIn' and \
                           lamp.name != 'superGame':
				lamp.schedule(schedule=lamp_schedules[i%32], cycle_seconds=0, now=False)
				i += 1

	def mode_stopped(self):
		pass
		
	def mode_tick(self):
		#self.layer.layers[0].enabled = (int(1.5 * time.time()) % 2) == 0
		pass

	def sw_enter_closed(self, sw):
		self.game.modes.add(self.game.service_mode)
		for lamp in self.game.lamps:
			lamp.disable()
		return True

		if self.game.machine_type != 'whitestar':
			self.add_switch_handler(name='exit', event_type='closed', delay=None, handler=self.exit_closed)

	def exit_closed(self, sw):
		return True

	def sw_down_closed(self, sw):
		volume = self.game.sound.volume_down()
		self.game.set_status("Volume Down : " + str(volume))
		return True

	def sw_up_closed(self, sw):
		volume = self.game.sound.volume_up()
		self.game.set_status("Volume Up : " + str(volume))
		return True


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

class TestGame(game.BasicGame):
	"""docstring for TestGame"""
	def __init__(self, machine_type):
		super(TestGame, self).__init__(machine_type)
		self.sound = SoundController(self)
		self.dmd = dmd.DisplayController(self, width=128, height=32, message_font=font_tiny7)

	def save_settings(self):
		pass
		
	def setup(self):
		"""docstring for setup"""
		self.settings = {}
		self.load_config(self.yamlpath)
		print("Initial switch states:")
		for sw in self.switches:
			print("  %s:\t%s" % (sw.name, sw.state_str()))

		self.attract_mode = Attract(self)

		self.sound.register_sound('service_enter', sound_path+"menu_in.wav")
		self.sound.register_sound('service_exit', sound_path+"menu_out.wav")
		self.sound.register_sound('service_next', sound_path+"next_item.wav")
		self.sound.register_sound('service_previous', sound_path+"previous_item.wav")
		self.sound.register_sound('service_switch_edge', sound_path+"switch_edge.wav")
		self.sound.register_sound('service_save', sound_path+"save.wav")
		self.sound.register_sound('service_cancel', sound_path+"cancel.wav")
		self.service_mode = procgame.service.ServiceMode(self,100,font_tiny7)
		self.reset()
		self.disable_popperL = 0
		
	def reset(self):
		super(TestGame, self).reset()
		self.modes.add(self.attract_mode)
		# Make sure flippers are off, especially for user initiated resets.
		self.enable_flippers(enable=False)
		
	def ball_starting(self):
		super(TestGame, self).ball_starting()
		
	def ball_ended(self):
		super(TestGame, self).ball_ended()
		
	def game_ended(self):
		super(TestGame, self).game_ended()
		self.modes.add(self.attract_mode)
		self.deadworld.mode_stopped()
		# for mode in copy.copy(self.modes.modes):
		# 	self.modes.remove(mode)
		# self.reset()
		self.set_status("Game Over")
		
	def dmd_event(self):
		"""Called by the GameController when a DMD event has been received."""
		self.dmd.update()

	def set_status(self, text):
		self.dmd.set_message(text, 3)
		print(text)
		
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
	 	game = TestGame(machine_type)
		game.yamlpath = yamlpath
		game.setup()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()
