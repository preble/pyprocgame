try:
	print("Initializing sound...")
	from pygame import mixer # This call takes a while.
except ImportError, e:
	print("Error importing pygame.mixer; sound will be disabled!  Error: "+str(e))

import os.path

class SoundController(object):
	"""Wrapper for pygame sound."""
	def __init__(self, delegate):
		super(SoundController, self).__init__()
		mixer.init()
		self.sounds = {}
		self.music = {}
		self.music_volume_offset = 0
		self.set_volume(0.5)

	def play_music(self, key, loops=0, start_time=0.0):
		"""Start playing music at the given *key*."""
		if key in self.music:
			self.load_music(key)
			mixer.music.play(loops,start_time)

	def stop_music(self):
		"""Stop the currently-playing music."""
		mixer.music.stop()

	def fadeout_music(self, time_ms = 750):
		""" """
		mixer.music.fadeout(time_ms)

	def load_music(self, key):
		""" """
		mixer.music.load(self.music[key])

	def register_sound(self, key, sound_file):
		""" """
		if os.path.isfile(sound_file):
			self.new_sound = mixer.Sound(str(sound_file))
               		self.sounds[key] = self.new_sound
			self.sounds[key].set_volume(self.volume)
		else:
			print ("Sound registration error: file %s does not exist!" % sound_file)

	def register_music(self, key, music_file):
		""" """
		if os.path.isfile(music_file):
                	self.music[key] = music_file
		else:
			print ("Music registration error: file %s does not exist!" % music_file)

	def play(self,key, loops=0, max_time=0, fade_ms=0):
		""" """
		if key in self.sounds:
			self.sounds[key].play(loops,max_time,fade_ms)

	def stop(self,key, loops=0, max_time=0, fade_ms=0):
		""" """
		if key in self.sounds:
			self.sounds[key].stop()

	def volume_up(self):
		""" """
		if (self.volume < 0.8):
			self.set_volume(self.volume + 0.1)
		return self.volume*10

	def volume_down(self):
		""" """
		if (self.volume > 0.2):
			self.set_volume(self.volume - 0.1)
		return self.volume*10

	def set_volume(self, new_volume):
		""" """
		self.volume = new_volume
		mixer.music.set_volume (new_volume + self.music_volume_offset)
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

