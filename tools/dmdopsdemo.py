import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import pinproc
import procgame
from procgame import *
import time

# dmdopsdemo.py demonstrates how to use Layer.composite_op.

class Game(game.BasicGame):
	"""Very simple game to get our DMD running."""
	def __init__(self, machine_type):
		super(Game, self).__init__(machine_type)
		self.dmd = dmd.DisplayController(self, width=128, height=32)
		self.frame_count = 0
	def dmd_event(self):
		"""Called by the GameController when a DMD event has been received."""
		self.dmd.update()
		if self.frame_count == 0:
			self.first_frame_time = time.time()
		self.frame_count += 1
		if self.frame_count == 200:
			secs = time.time() - self.first_frame_time
			print "%d frames, %0.2f seconds, %0.2ffps" % (self.frame_count, secs, self.frame_count/secs)
		
	def play(self, anim):
		font = dmd.font_named('Font18x12.dmd')
		mode = game.Mode(self, 9)
		anim_layer = dmd.AnimatedLayer(frames=anim.frames, repeat=True, hold=False)
		text_layer = dmd.TextLayer(128/2, 8, font, 'center').set_text('EXTRA BALL')
		text_layer.composite_op = 'sub'
		mode.layer = dmd.GroupedLayer(width=128, height=32)
		mode.layer.layers += [anim_layer]
		mode.layer.layers += [text_layer]
		self.modes.add(mode)
	
def main():
	if len(sys.argv) < 2:
		print("Usage: %s <file.dmd>"%(sys.argv[0]))
		return

	filename = sys.argv[1]
	anim = dmd.Animation().load(filename)
	if anim.width != 128 or anim.height != 32:
		raise ValueError, "Expected animation dimensions to be 128x32."

	game = Game('custom')
	game.play(anim=anim)
	
	print("Displaying %d frame(s) looped." % (len(anim.frames)))
	game.run_loop()

if __name__ == "__main__":
	main()
