import sys
import os
import procgame.dmd
import time
import re
import string
import Image

import logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def dmd_to_image(src_filename, dst_filename):
	anim = procgame.dmd.Animation().load(src_filename)
	image = Image.new(mode='L', size=(anim.width, anim.height))
	pixels = []
	frame = anim.frames[0]
	for y in range(anim.height):
		for x in range(anim.width):
			color = frame.get_dot(x, y)
			pixels.append((color & 0xf) << 4)
	image.putdata(pixels)
	image.save(dst_filename)

def tool_populate_options(parser):
    pass

def tool_get_usage():
    return """[options] <input.dmd> <outputimage>"""

def tool_run(options, args):
	if len(args) < 2:
		return False
	dmd_to_image(src_filename=args[0], dst_filename=args[1])
	return True
