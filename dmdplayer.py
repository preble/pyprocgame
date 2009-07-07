import pinproc
import procgame
from procgame import *
import sys
import time

# dmdplayer.py demonstrates how to load and display a sequence of DMD frames.

def main():
	if len(sys.argv) < 2:
		print("Usage: %s <file.dmd>"%(sys.argv[0]))
		return

	filename = sys.argv[1]
	anim = dmd.Animation().load(filename)
	if anim.width != 128 or anim.height != 32:
		raise ValueError, "Expected animation dimensions to be 128x32."

	proc = pinproc.PinPROC('wpc')
	proc.reset(1)
	
	print("Displaying %d frame(s) looped." % (len(anim.frames)))
	
	while True:
		for frame in anim.frames:
			proc.dmd_draw(frame)
			time.sleep(0.1)

if __name__ == "__main__":
	main()