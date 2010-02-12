print("Initializing sound...")
from pygame import mixer # This call takes a while.
import os.path

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

	def play_music(self, key, loops=0, start_time=0.0):
		if self.music[key] != 'no_file':
			self.load_music(key)
			mixer.music.play(loops,start_time)

	def stop_music(self):
		mixer.music.stop()

	def fadeout_music(self, time_ms = 750):
		mixer.music.fadeout(time_ms)

	def load_music(self, key):
		mixer.music.load(self.music[key])

	def register_sound(self, key, sound_file):
		if not key in self.sounds:
			if os.path.isfile(sound_file):
				self.new_sound = mixer.Sound(str(sound_file))
                		self.sounds[key] = self.new_sound
				self.sounds[key].set_volume(self.volume)
			else:
				self.sounds[key] = 'no_file'
				print ("Sound registration error: file %s does not exist!" % sound_file)

	def register_music(self, key, music_file):
		if os.path.isfile(music_file):
                	self.music[key] = music_file
		else:
			self.music[key] = 'no_file'
			print ("Music registration error: file %s does not exist!" % music_file)

	def play(self,key, loops=0, max_time=0, fade_ms=0):
		if self.sounds[key] != 'no_file':
			self.sounds[key].play(loops,max_time,fade_ms)

	def stop(self,key, loops=0, max_time=0, fade_ms=0):
		if self.sounds[key] != 'no_file':
			self.sounds[key].stop()

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

