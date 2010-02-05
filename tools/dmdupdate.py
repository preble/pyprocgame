import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame.dmd
import time

def update(filename):
	"""Updated the given .dmd file from legacy dot formats to the modern 0x0-0xf format."""
	anim = procgame.dmd.Animation()
	anim.load(filename)
	upgrade_frames = anim.frames
	if len(upgrade_frames) == 2:
		upgrade_frames = upgrade_frames[:1] # assume it's a font; only do the first frame
	for frame in upgrade_frames:
		for x in range(frame.width):
			for y in range(frame.height):
				dot = frame.get_dot(x, y)
				if 0 <= dot <= 3:
					dot *= 5
				else:
					dot -= 0xF
				frame.set_dot(x, y, dot)
	anim.save(filename)

def main():
	if len(sys.argv) < 2:
		print("Usage: %s <file.dmd>"%(sys.argv[0]))
		return
	update(filename=sys.argv[1])


if __name__ == "__main__":
	main()