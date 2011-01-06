import sys
import os
import pinproc
from procgame import dmd
import time

# dmdplayer.py demonstrates how to load and display a sequence of DMD frames.

def play(filename):
	anim = dmd.Animation().load(filename)
	if anim.width != 128 or anim.height != 32:
	    print("Dimentions are %dx%d; expected 128x32." % (anim.width, anim.height))
	    return False
	
	proc = pinproc.PinPROC(pinproc.MachineTypeCustom)
	layer = dmd.AnimatedLayer(frames=anim.frames, repeat=False, hold=False)
	while True:
		for event in proc.get_events():
			if event['type'] == pinproc.EventTypeDMDFrameDisplayed:
				frame = layer.next_frame()
				if frame == None:
					sys.exit(0)
				proc.dmd_draw(frame)
				if len(layer.frames) == 0:
					proc.dmd_draw(frame)
					proc.dmd_draw(frame)
					proc.dmd_draw(frame)
	
	return True


def tool_populate_options(parser):
    pass

def tool_get_usage():
    return """<file.dmd>"""

def tool_run(options, args):
    if len(args) != 1:
        return False
    return play(filename=args[0])
