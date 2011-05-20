import sys
import os
import procgame.dmd
import time
import re
import string

import logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def load_and_append_image(anim, filename):
	if not os.path.exists(filename):
		return False
	print "Appending", filename
	
	tmp = procgame.dmd.Animation().load(filename, allow_cache=False)
	if len(tmp.frames) > 0:
		first_frame = tmp.frames[0]
		anim.width, anim.height = first_frame.width, first_frame.height
	anim.frames += tmp.frames
	
	return True


def load_and_append_text(anim, filename, dot_map = {'0':0, '1':5, '2':10, '3':15}):
	"""Support for text-based DMD files.  Each line in the file describes a
	row of DMD data, with each character representing a dot.  Dot values are
	interpreted using the dot_map parameter.  A blank line indicates the end
	of a frame.
	"""
	if not os.path.exists(filename):
		return False
	print "Appending ", filename
	f = open(filename, 'r')
	lines = f.readlines()
	
	# Find the dimensions
	w = 0
	h = 0
	for line in lines:
		line = string.strip(line)
		if len(line) == 0: break
		w = len(line)
		h += 1
	print "Dimensions:", w, h
	(anim.width, anim.height) = (w, h)
	
	frame = procgame.dmd.Frame(w, h)
	y = 0
	
	for line in lines:
		
		line = string.strip(line)
		
		if len(line) == 0:
			anim.frames.append(frame)
			frame = procgame.dmd.Frame(w, h)
			y = 0
			continue
		
		x = 0
		for ch in line:
			frame.set_dot(x, y, dot_map[ch])
			x += 1
		
		y += 1
	
	if y != 0:
		anim.frames.append(frame)
	
	return True


def image_to_dmd(src_filenames, dst_filename):
	"""docstring for image_to_dmd"""
	last_filename = None
	anim = procgame.dmd.Animation()
	
	if len(src_filenames) == 1 and re.search("%[0-9]*d", src_filenames[0]):
		pattern = src_filenames[0]
		src_filenames = []
		for frame_index in range(1000):
			src_filenames.append(pattern % (frame_index))
	else:
		for filename in src_filenames:
			if not os.path.exists(filename):
				print 'File not found:', filename
	
	for filename in src_filenames:
		if filename.endswith('.txt'):
			load_and_append_text(anim=anim, filename=filename)
		else:
			load_and_append_image(anim=anim, filename=filename)
	
	if len(anim.frames) == 0:
		print "ERROR: No frames found!  Ensure that the source file(s) exist and are readable."
		sys.exit(1)
	
	anim.save(dst_filename)
	print "Saved."


def tool_populate_options(parser):
    pass

def tool_get_usage():
    return """[options] <image1.png> [... <imageN.png>] <output.dmd>

  If only one image name is used it may include %d format specifiers to
  create animations.  For example, to create an animation of up to 999 
  frames with sequential names:
  
    Animation%03d.png Animation.dmd
  
  Note that in UNIX-like shells that support wildcard expansion you can
  enter image*.png as the one image filename and the shell will expend it
  to include all filenames matching that wildcard."""

def tool_run(options, args):
	if len(args) < 2:
		return False
	image_to_dmd(src_filenames=args[0:-1], dst_filename=args[-1])
	return True
