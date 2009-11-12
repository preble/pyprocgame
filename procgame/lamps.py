# Experimental code by Adam Preble, September 23, 2009.
# 
from game import *
import random
import string
import math
import copy
import re


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
	str = re.sub('(\[[\- ]*\])', lambda m: '.'*len(m.group(1)), str)
	str = re.sub('(\<[\- ]*\])', lambda m: fade_in(len(m.group(1)))[:-1] + '.', str)
	str = re.sub('(\[[\- ]*\>)', lambda m: '.'+fade_out(len(m.group(1)))[1:], str)
	str = re.sub('(\<[\- ]*\>)', lambda m: fade_fade(len(m.group(1))), str)
	return str
# End of Pattern functions

class LampShowTrack(object):
	"""docstring for LampShowTrack"""
	def __init__(self, line):
		super(LampShowTrack, self).__init__()
		self.name = ''
		self.schedules = []
		self.load_from_line(line)
		self.current_index = 0
	
	def load_from_line(self, line):
		line_re = re.compile('(?P<name>\w+)\s*\| (?P<data>.*)$')
		m = line_re.match(line)
		if m == None:
			raise ValueError, "Regexp didn't match on track line: "+line
		self.name = m.group('name')
		data = m.group('data')+(' '*32) # Pad it with 32 spaces so that the FIXME below doesn't cause a problem.
		data = expand_line(data)
		bits = 0
		bit_count = 0
		ignore_first = True
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
		print "%s | %s" % (self.name, m.group('data'))
		print "%s | %s" % (self.name, data)

	def reset(self):
		self.schedules = []
		self.current_index = 0

	def restart(self):
		self.current_index = 0
	
	def next_schedule(self):
		if self.is_complete():
			return 0
		self.current_index += 1
		return self.schedules[self.current_index-1]
	
	def is_complete(self):
		return self.current_index >= len(self.schedules)

class LampShow(object):
	
	"""docstring for LampShow"""
	def __init__(self, game):
		super(LampShow, self).__init__()
		self.game = game
		self.reset()

	def reset(self):
		#for tr in self.tracks:
		#	tr.reset()	
		self.tracks = []
		self.t0 = None
		self.last_time = -.5
		
	def load(self, filename):
		f = open(filename, 'r')
		for line in f.readlines():
			if line[0] != '#':
				self.tracks.append(LampShowTrack(line))
		
	def tick(self):
		if self.t0 == None:
			self.t0 = time.time()
		new_time = (time.time() - self.t0)
		seconds = int(new_time)
		time_diff = new_time - self.last_time
		if (time_diff > 0.500):
			self.last_time = new_time
			for tr in self.tracks:
				sch = tr.next_schedule()
				self.game.lamps[tr.name].schedule(schedule=sch, cycle_seconds=1, now=True)
			print time.time()

	def restart(self):
		for tr in self.tracks:
			tr.restart()
		#self.t0 = None
		#self.last_seconds = -1
	
	def is_complete(self):
		for tr in self.tracks:
			if tr.is_complete() == False:
				return False
		return True

class LampShowMode(Mode):
	"""Keeps track of ball save timer."""
	def __init__(self, game):
		super(LampShowMode, self).__init__(game, 3)
		self.lampshow = LampShow(self.game)
		self.show_over = True

	def load(self, filename, repeat=False, callback='None'):
		self.callback = callback
		self.repeat = repeat
		self.lampshow.reset()
		self.lampshow.load(filename)
		self.restart()

	def restart(self):
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
	"""docstring for TestGame"""
	def __init__(self, game):
		self.game = game
		self.shows = {}
		self.show = LampShowMode(self.game)
		self.show_playing = False
		
	def register_show(self, key, show_file):
                self.shows[key] = show_file

	def play_show(self, key, repeat=False, callback='None'):
		# Always stop any previously running show first.
		self.stop_show()
		self.show.load(self.shows[key], repeat, callback)
		self.game.modes.add(self.show)
		self.show_playing = True

	def stop_show(self):
		if self.show_playing:
			self.game.modes.remove(self.show)
		self.show_playing = False

