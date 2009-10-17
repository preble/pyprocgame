import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import pinproc
import procgame
from procgame import *
import time

# dmdfont.py Displays the given text on the DMD with the given text.

def main():
	if len(sys.argv) < 3:
		print("Usage: %s <font.dmd> <text>"%(sys.argv[0]))
		return

	font = dmd.Font(sys.argv[1])
	if not font:
		print("Error loading font")
		return
	text = sys.argv[2]
	
	text_layer = dmd.TextLayer(0, 0, font)
	text_layer.set_text(text)

	proc = pinproc.PinPROC('wpc')
	w = 128
	h = 32
	proc.reset(1)
	
	grouped_layer = dmd.GroupedLayer(w, h, [dmd.FrameLayer(frame=dmd.Frame(w, h)), text_layer])
	
	frame = grouped_layer.next_frame()
	if frame == None:
		print("No frame?")
		return
	for x in range(3): # Send it enough times to get it to show
		proc.dmd_draw(frame)

if __name__ == "__main__":
	main()