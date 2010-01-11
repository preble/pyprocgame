import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import pinproc
import procgame
from procgame import *
import time

# dmdpan.py: Demonstrates how to load a large .dmd image and pan it about on the DMD.

class PanningLayer(dmd.Layer):
	"""Pans a frame about on a 128x32 buffer, bouncing when it reaches the boundaries."""
	def __init__(self, width, height, frame, origin, translate):
		super(PanningLayer, self).__init__()
		self.buffer = dmd.Frame(width, height)
		self.frame = frame
		self.origin = origin
		self.translate = translate
		self.tick = 0
		# Make sure the translate value doesn't cause us to do any strange movements:
		if width == frame.width:
			self.translate = (0, self.translate[1])
		if height == frame.height:
			self.translate = (self.translate[0], 0)
	
	def next_frame(self):
		self.tick += 1
		if (self.tick % 6) != 0:
			return self.buffer
		dmd.Frame.copy_rect(dst=self.buffer, dst_x=0, dst_y=0, src=self.frame, src_x=self.origin[0], src_y=self.origin[1], width=self.buffer.width, height=self.buffer.height)
		if (self.origin[0] + self.buffer.width + self.translate[0] > self.frame.width) or (self.origin[0] + self.translate[0] < 0):
			self.translate = (self.translate[0] * -1, self.translate[1])
		if (self.origin[1] + self.buffer.height + self.translate[1] > self.frame.height) or (self.origin[1] + self.translate[1] < 0):
			self.translate = (self.translate[0], self.translate[1] * -1)
		self.origin = (self.origin[0] + self.translate[0], self.origin[1] + self.translate[1])
		return self.buffer

class Game(game.GameController):
	"""Very simple game to get our DMD running."""
	def __init__(self, machineType):
		super(Game, self).__init__(machineType)
		self.dmd = dmd.DisplayController(self, width=128, height=32)
	def dmd_event(self):
		"""Called by the GameController when a DMD event has been received."""
		self.dmd.update()
	def pan(self, frame, origin, translate):
		mode = game.Mode(self, 9)
		mode.layer = PanningLayer(width=128, height=32, frame=frame, origin=origin, translate=translate)
		self.modes.add(mode)

def main():
	if len(sys.argv) < 2:
		print("Usage: %s <file.dmd>"%(sys.argv[0]))
		return

	filename = sys.argv[1]
	anim = dmd.Animation().load(filename)
	if anim.width < 128 and anim.height < 32:
		raise ValueError, "Expected animation dimensions to be 128x32 (on one side)"

	game = Game('wpc')
	
	game.pan(frame=anim.frames[0], origin=(0,0), translate=(1,1))
	
	game.run_loop()


if __name__ == "__main__":
	main()
