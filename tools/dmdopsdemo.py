import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import pinproc
import procgame
from procgame import *
import time

# dmdplayer.py demonstrates how to load and display a sequence of DMD frames.


class Game(game.GameController):
	"""Very simple game to get our DMD running."""
	def __init__(self, machineType):
		super(Game, self).__init__(machineType)
		self.dmd = dmd.DisplayController(self, width=128, height=32)
	def dmd_event(self):
		"""Called by the GameController when a DMD event has been received."""
		self.dmd.update()
	def play(self, anim):
		font = dmd.Font("../shared/dmd/Jazz18-18px.dmd")
		# font = dmd.Font("../shared/dmd/Font09Bx7.dmd")
		mode = game.Mode(self, 9)
		anim_layer = dmd.AnimatedLayer(frames=anim.frames, frame_time=3, repeat=True, hold=False)
		text_layer = dmd.TextLayer(128/2, 7, font, 'center').set_text('EXTRA BALL')
		text_layer.composite_op = 'add'
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
