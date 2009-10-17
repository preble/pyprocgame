# Experimental code by Adam Preble, September 23, 2009.
# 
import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame
import pinproc
from procgame import *
from threading import Thread
import random
import string
import time
import locale
import yaml
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
		for ch in data:
			bits >>= 1
			bit_count += 1
			if ch != " ":
				bits |= 1 << 31
			if bit_count == 32:
				self.schedules.append(bits)
				bits = 0
				bit_count = 0
		# FIXME: This lops off the last up to 31 bits of track data!
		# Print out all of the data for debugging purposes:
		# print "Loaded %d schedules for %s:" % (len(self.schedules), self.name)
		# for sch in self.schedules:
		# 	print " - % 8x" % (sch)
		print "%s | %s" % (self.name, m.group('data'))
		print "%s | %s" % (self.name, data)
	
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
		self.tracks = []
		self.t0 = None
		self.last_seconds = -1
		
	def load(self, filename):
		f = open(filename, 'r')
		for line in f.readlines():
			if line[0] != '#':
				self.tracks.append(LampShowTrack(line))
		
	def tick(self):
		if self.t0 == None:
			self.t0 = time.time()
		seconds = int((time.time() - self.t0))
		if (seconds != self.last_seconds):
			self.last_seconds = seconds
			for tr in self.tracks:
				sch = tr.next_schedule()
				self.game.lamps[tr.name].schedule(schedule=sch, cycle_seconds=1, now=True)
			print time.time()
	
	def is_complete(self):
		for tr in self.tracks:
			if tr.is_complete() == False:
				return False
		return True

def main():
	if len(sys.argv) < 3:
		print("Usage: %s <lampshow> <yaml>"%(sys.argv[0]))
		return

	filename = sys.argv[1]
	yamlpath = sys.argv[2]

        # Parse YAML file just to get the machine type so we know what type of GameController
        # to create.
         
        config = yaml.load(open(yamlpath, 'r'))
        sect_dict = config['PRGame']
        machineType = sect_dict['machineType']
        print("Machine type is %s"%(machineType))
	
	g = game.GameController(str(machineType))
	g.load_config(yamlpath)
	
	show = LampShow(game=g)
	show.load(filename)

	while not show.is_complete():
		time.sleep(0.03)
		show.tick()
		#g.lamps.gi01.schedule(schedule=0xffffffff, cycle_seconds=1, now=True) # commented out test code
		g.proc.watchdog_tickle()

if __name__ == "__main__":
	main()
