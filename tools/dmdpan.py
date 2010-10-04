import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import pinproc
import procgame
from procgame import *
import time

# dmdpan.py: Demonstrates how to load a large .dmd image and pan it about on the DMD.

class Game(game.BasicGame):
	"""Very simple game to get our DMD running."""
	def __init__(self, machine_type):
		super(Game, self).__init__(machine_type)

	def pan(self, frame, origin, translate):
		mode = game.Mode(self, 9)
		mode.layer = dmd.PanningLayer(width=128, height=32, frame=frame, origin=origin, translate=translate)
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
