import random
import time
import logging

try:
	logging.getLogger('game.sound').info("Initializing sound...")
	from pygame import mixer # This call takes a while.
except ImportError, e:
	logging.getLogger('game.sound').error("Error importing pygame.mixer; sound will be disabled!  Error: "+str(e))

import os.path

class SoundController(object):
	"""Wrapper for pygame sound."""
	
	enabled = True
	
	def __init__(self, delegate):
		super(SoundController, self).__init__()
		self.logger = logging.getLogger('game.sound')
		try:
			mixer.init()
		except Exception, e:
			# The import mixer above may work, but init can still fail if mixer is not fully supported.
			self.enabled = False
			self.logger.error("pygame mixer init failed; sound will be disabled: "+str(e))
		self.sounds = {}
		self.music = {}
		self.music_volume_offset = 0
		self.set_volume(0.5)
		self.voice_end_time = 0

	def play_music(self, key, loops=0, start_time=0.0):
		"""Start playing music at the given *key*."""
		if not self.enabled: return
		if key in self.music:
			if len(self.music[key]) > 0:
				random.shuffle(self.music[key])
			self.load_music(key)
			mixer.music.play(loops,start_time)

	def stop_music(self):
		"""Stop the currently-playing music."""
		if not self.enabled: return
		mixer.music.stop()

	def fadeout_music(self, time_ms = 450):
		""" """
		if not self.enabled: return
		mixer.music.fadeout(time_ms)

	def load_music(self, key):
		""" """
		if not self.enabled: return
		mixer.music.load(self.music[key][0])

	def register_sound(self, key, sound_file):
		""" """
		self.logger.info("Registering sound - key: %s, file: %s", key, sound_file)
		if not self.enabled: return
		if os.path.isfile(sound_file):
			self.new_sound = mixer.Sound(str(sound_file))
			self.new_sound.set_volume(self.volume)
			if key in self.sounds:
				if not self.new_sound in self.sounds[key]:
					self.sounds[key].append(self.new_sound)
			else:
				self.sounds[key] = [self.new_sound]
		else:
			self.logger.error("Sound registration error: file %s does not exist!", sound_file)

	def register_music(self, key, music_file):
		""" """
		if not self.enabled: return
		if os.path.isfile(music_file):
			if key in self.music:
				if not music_file in self.music[key]:
					self.music[key].append(music_file)
			else:
				self.music[key] = [music_file]
		else:
			self.logger.error("Music registration error: file %s does not exist!", music_file)

	def play(self,key, loops=0, max_time=0, fade_ms=0):
		""" """
		if not self.enabled: return
		if key in self.sounds:
			if len(self.sounds[key]) > 0:
				random.shuffle(self.sounds[key])
			self.sounds[key][0].play(loops,max_time,fade_ms)
			return self.sounds[key][0].get_length()
		else:
			return 0

	def play_voice(self,key, loops=0, max_time=0, fade_ms=0):
		""" """
		if not self.enabled: return 0
		current_time = time.time()

		# Make sure previous voice call is finished.
		if current_time < self.voice_end_time: return 0
		if key in self.sounds:
			if len(self.sounds[key]) > 0:
				random.shuffle(self.sounds[key])
			self.sounds[key][0].play(loops,max_time,fade_ms)
			duration = self.sounds[key][0].get_length() * (loops+1)
			self.voice_end_time = current_time + duration
			return duration
		else:
			return 0

	def stop(self,key, loops=0, max_time=0, fade_ms=0):
		""" """
		if not self.enabled: return
		if key in self.sounds:
			self.sounds[key][0].stop()

	def volume_up(self):
		""" """
		if not self.enabled: return
		if (self.volume < 0.8):
			self.set_volume(self.volume + 0.1)
		return self.volume*10

	def volume_down(self):
		""" """
		if not self.enabled: return
		if (self.volume > 0.2):
			self.set_volume(self.volume - 0.1)
		return self.volume*10

	def set_volume(self, new_volume):
		""" """
		if not self.enabled: return
		self.volume = new_volume
		mixer.music.set_volume (new_volume + self.music_volume_offset)
		for key in self.sounds:
			for sound in self.sounds[key]:
				sound.set_volume(self.volume)

	def beep(self):
		if not self.enabled: return
		pass
		#	self.play('chime')
