# Experimental code by Adam Preble, September 23, 2009.
# 
import game
import random
import string
import math
import copy
import re
import time
import logging

# Pattern functions:
def make_pattern(m, repeats):
	"""docstring for make_pattern"""
	str = ''
	for i in range(m):
		for j in range(repeats):
			str += ' ' + (i + 1) * '.'
	return str
def make_pattern_of_length(l):
	"""docstring for make_pattern_of_length"""
	# repeats = max(1, l / 26)
	# return make_pattern(4, repeats)[:l] # Guarantee it ends with a .
	s = '.  .  . . .. .. ... ... .... .... ..... .....'[:l]
	if len(s) < l:
		s += '.' * (l-len(s))
	return s
def fade_in(l):
	return make_pattern_of_length(l)
def fade_out(l):
	s = fade_in(l)
	s = s[::-1]
	return s
def fade_fade(l):
	"""docstring for fade_fade"""
	a = fade_in(l/2)
	b = fade_out(l/2)
	if (l % 2) == 0:
		return a[:-1] + ' ' + b
	else:
		return a + ' ' + b
def expand_line(str):
	"""Expands special characters ``<>[]`` within *str* and returns the dots-and-spaces representation.  
	Used by :class:`LampShowTrack`.
	"""
	str = re.sub('(\[[\- ]*\])', lambda m: '.'*len(m.group(1)), str)
	str = re.sub('(\<[\- ]*\])', lambda m: fade_in(len(m.group(1)))[:-1] + '.', str)
	str = re.sub('(\[[\- ]*\>)', lambda m: '.'+fade_out(len(m.group(1)))[1:], str)
	str = re.sub('(\<[\- ]*\>)', lambda m: fade_fade(len(m.group(1))), str)
	return str
# End of Pattern functions

class LampShowTrack(object):
	"""A series of schedules to be applied to a driver over a period of time, usually in concert with other tracks
	to make up a :class:`LampShow`.
	
	Tracks are initialized from a string with three parts:
	
		1. An identifier describing the driver to be manipulated by this track.  
		   If the identifier has a ``lamp:`` prefix the text following it is interpreted as a lamp name 
		   (member of :attr:`~procgame.game.GameController.lamps`); ``coil:`` corresponds to members of :attr:`~procgame.game.GameController.coils`.
		   If neither of these prefixes is present then the name is assumbed to be a lamp name.
		2. A pipe character (``|``).
		3. A sequence of characters describing the lighting/activation pattern for the driver.
		   In the simplest case such a string would be a series of dots/periods (``'.'``) and spaces.
	
	For example, a lamp show track describing a lamp (named Bonus5X) that would blink on and off might be::
	
	    lamp:Bonus5X | ....    ....    ....    ....
	
	Each character in a track represents 1/32nd of a second.  This corresponds to the 32 schedule bits of a :class:`~procgame.game.Driver`.
	
	Special characters may be used in place of dots as shorthand for effects such as fades or simply holding a driver on.
	This makes constructing and tuning large shows much less time-consuming.  Four characters may be used:
	
		| ``[`` -- open with a "hold on"
		| ``]`` -- close with a "hold on"
		| ``<`` -- open with a fade-in
		| ``>`` -- close with a fade-out
	
	Each open must be balanced with a close, although it need not be of the same type.  
	For example, to fade on a lamp and then keep it on::
	
		lamp:Bonus5X |    <                  ][                 ]
	
	This is translated (by :func:`expand_line`) to something similar to this::
	
		lamp:Bonus5X |    .  .  .. .. ... .......................
	
	Or, to pulse it in a fade-in-fade-out pattern::
	
		lamp:Bonus5X |       <                     >
	
	To pulse a flasher rapidly::
	
		coil:Flasher2 |       .      .     .     .    .
	
	These special characters may be mixed with the simpler dots and spaces, but there must always be spaces between
	the open and close characters.  Note that the fade effect is not exactly a fade, but rather turning the driver
	on and off very rapidly to simulate the lamp getting brighter or darker.
	
	.. warning::
	
		Care must be used when constructing lamp shows controlling coils.  Never hold a coil or flasher active
		for an extended period of time.  Otherwise the game will blow a fuse, burn a coil/flasher, or worse.
	
	"""
	
	name = ''
	"""Name of this track which corresponds to a driver."""
	
	schedules = []
	"""Sequence of 32-bit schedule values."""
	
	current_index = 0
	"""Index into the :attr:`schedules` list."""
	
	driver = None
	"""The :class:`~procgame.game.Driver` correspopnding to this track."""
	
	def __init__(self, line):
		super(LampShowTrack, self).__init__()
		self.load_from_line(line)
	
	def load_from_line(self, line):
		line_re = re.compile('(?P<name>\S+)\s*\| (?P<data>.*)$')
		m = line_re.match(line)
		if m == None:
			raise ValueError, "Regexp didn't match on track line: "+line
		self.name = m.group('name')
		data = m.group('data')+(' '*32) # Pad it with 32 spaces so that the FIXME below doesn't cause a problem.
		data = expand_line(data)
		bits = 0
		bit_count = 0
		ignore_first = True
		self.schedules = []
		for ch in data:
			bits >>= 1
			bit_count += 1
			if ch != " ":
				bits |= 1 << 31
			if bit_count % 16 == 0:
				if not ignore_first:
					self.schedules.append(bits)
					#bits = 0
					#bit_count = 0
				ignore_first = False
		# FIXME: This lops off the last up to 31 bits of track data!
		# Print out all of the data for debugging purposes:
		# print "Loaded %d schedules for %s:" % (len(self.schedules), self.name)
		# for sch in self.schedules:
		# 	print " - % 8x" % (sch)
		# print "%s | %s" % (self.name, m.group('data'))
		# print "%s | %s" % (self.name, data)

	def resolve_driver_with_game(self, game):
		if self.name.startswith('coil:'):
			self.driver = game.coils[self.name[5:]]
		elif self.name.startswith('lamp:'):
			self.driver = game.lamps[self.name[5:]]
		else: # lamps are the default:
			self.driver = game.lamps[self.name]

	def reset(self):
		"""Clears the contents of this track."""
		self.schedules = []
		self.current_index = 0

	def restart(self):
		"""Restarts this track at the beginning."""
		self.current_index = 0
	
	def next_schedule(self):
		if self.is_complete():
			return 0
		self.current_index += 1
		return self.schedules[self.current_index-1]
	
	def is_complete(self):
		"""True if this track's schedules have all been used."""
		return self.current_index >= len(self.schedules)

class LampShow(object):
	"""Manages loading and playing a lamp show consisting of several lamps (or other drivers), 
	each of which is a track (:class:`LampShowTrack`, to be precise)."""
	
	def __init__(self, game):
		super(LampShow, self).__init__()
		self.game = game
		self.reset()

	def reset(self):
		"""Clears out all of the tracks in this lamp show."""
		#for tr in self.tracks:
		#	tr.reset()	
		self.tracks = []
		self.t0 = None
		self.last_time = -.5
		
	def load(self, filename):
		"""Reads lines from the given ``filename`` in to create tracks within the lamp show.  A lamp show 
		generally consists of several lines of text, one for each driver, spaced so as to show a textual
		representation of the lamp activity over time.
		
		Lines that start with a '#' are ignored as comments.  An example (and very short) lamp show follows::
		
			lamp:Left   | ..      ..
			lamp:Center |   ..  ..  ..
			lamp:Right  |     ..      ..
		
		See :class:`LampShowTrack` for a complete description of the track line format.
		"""
		f = open(filename, 'r')
		for line in f.readlines():
			if line[0] != '#':
				self.tracks.append(LampShowTrack(line))
		
	def tick(self):
		"""Instructs the lamp show to advance based on the system clock and update the drivers associated with its tracks."""
		if self.t0 == None:
			self.t0 = time.time()
		new_time = (time.time() - self.t0)
		seconds = int(new_time)
		time_diff = new_time - self.last_time
		if (time_diff > 0.500):
			self.last_time = new_time
			for tr in self.tracks:
				if tr.driver == None: # Lazily set drivers.
					tr.resolve_driver_with_game(self.game)
				sch = tr.next_schedule()
				tr.driver.schedule(schedule=sch, cycle_seconds=1, now=True)
	
	def restart(self):
		"""Restart the show from the beginning."""
		for tr in self.tracks:
			tr.restart()
		#self.t0 = None
		#self.last_seconds = -1
	
	def is_complete(self):
		"""``True`` if each of the tracks has completed."""
		for tr in self.tracks:
			if tr.is_complete() == False:
				return False
		return True

class LampShowMode(game.Mode):
	""":class:`~procgame.game.Mode` subclass that manages a single :class:`LampShow`, 
	updating it in the :meth:`~procgame.game.Mode.mode_tick` method.
	"""
	def __init__(self, game):
		super(LampShowMode, self).__init__(game, 3)
		self.lampshow = LampShow(self.game)
		self.show_over = True
		self.logger = logging.getLogger('game.lamps')

	def load(self, filename, repeat=False, callback='None'):
		"""Load a new lamp show."""
		self.callback = callback
		self.repeat = repeat
		self.lampshow.reset()
		self.lampshow.load(filename)
		self.restart()

	def restart(self):
		"""Restart the lamp show."""
		self.lampshow.restart()
		self.show_over = False

	def mode_tick(self):
		if self.lampshow.is_complete() and not self.show_over:
			if self.repeat:
				self.restart()
			else:
				self.cancel_delayed('show_tick')
				self.show_over = True
				if self.callback != 'None':
					self.callback()
		elif not self.show_over:
			self.lampshow.tick()

class LampController(object):
	"""Controller object that encapsulates a :class:`LampShow` and helps to restore lamp drivers to their prior state."""
	
	shows = {}
	"""Dictionary of :class:`LampShow` objects."""
	
	show = None
	""":class:`LampShowMode` that must be added to the mode queue."""
	
	def __init__(self, game):
		self.game = game
		self.show = LampShowMode(self.game)
		self.show_playing = False
		self.saved_state_dicts = {}
		self.logger = logging.getLogger('game.lamps')
		
	def register_show(self, key, show_file):
                self.shows[key] = show_file

	def play_show(self, key, repeat=False, callback='None'):
		# Always stop any previously running show first.
		self.stop_show()
		self.show.load(self.shows[key], repeat, callback)
		self.game.modes.add(self.show)
		self.show_playing = True

	def restore_callback(self):
		self.resume_state = False
		self.restore_state(self.resume_key)
		self.callback()

	def stop_show(self):
		if self.show_playing:
			self.game.modes.remove(self.show)
		self.show_playing = False

	def save_state(self, key):
		state_dict = {}
		for lamp in self.game.lamps:
			state_dict[lamp.name] = {'time':lamp.last_time_changed, 'state':lamp.state()}
		self.saved_state_dicts[key] = state_dict
		self.saved_state_dicts[key + '_time'] = time.time()

	def restore_state(self, key):
		self.logger.info('Restoring lamp state "%s"...', key)
		if key in self.saved_state_dicts:
			state_dict = self.saved_state_dicts[key]
			for lamp_name, record in state_dict.iteritems():
				# For now, only use schedules.  This won't work with pulses lamps... probably needs to be fixed.
				# So, ignore GIs for now.
				if lamp_name.find('gi0', 0) == -1:
					time_remaining =  (record['state']['outputDriveTime'] + record['time']) - \
					                  self.saved_state_dicts[key + '_time']
					# Disable the lamp if it has never been used or if there would have
					# been less than 1 second of drive time when the state was saved.
					if (record['time'] == 0 or time_remaining < 1.0) and record['state']['outputDriveTime'] != 0:
						self.game.lamps[lamp_name].disable()
					# Otherwise, resume the lamp
					else:
						if record['state']['outputDriveTime'] == 0:
							duration = 0
						else:
							duration = int(time_remaining)
						if record['state']['timeslots'] == 0:
							self.game.lamps[lamp_name].disable()
						else:
							self.game.lamps[lamp_name].schedule(record['state']['timeslots'], \
                                                                    duration, \
                                                                    record['state']['waitForFirstTimeSlot'])
