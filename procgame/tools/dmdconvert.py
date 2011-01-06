import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame.dmd
import time
#import pygame.image
import Image
import re
import string

class ImageSequence:
	"""Iterates over all images in a sequence (of PIL Images)."""
	# Source: http://www.pythonware.com/library/pil/handbook/introduction.htm
	def __init__(self, im):
		self.im = im
	def __getitem__(self, ix):
		try:
			if ix:
				self.im.seek(ix)
			return self.im
		except EOFError:
			raise IndexError # end of sequence

def gif_frames(src):
	"""Returns an array of frames to be added to the animation."""
	frames = []
	
	# We have to do some special stuff for animated GIFs: check for the background index, and if we get it use the last frame's value.
	transparent_idx = -1
	background_idx = -1
	if 'transparency' in src.info:
		transparent_idx = src.info['transparency']
	if 'background' in src.info:
		background_idx = src.info['background']
	last_frame = None
	
	(w, h) = src.size
	
	for src_im in ImageSequence(src):
		reduced = src.convert("L") #.quantize(palette=pal_im).convert("P", palette=Image.ADAPTIVE, colors=4)#
		
		frame = procgame.dmd.Frame(w, h)
		
		for x in range(w):
			for y in range(h):
				idx = src_im.getpixel((x, y)) # Get the palette index for this pixel
				if idx == background_idx and last_frame != None:
					if last_frame == None:
						color = 0xff # Don't have a good option here.
					else:
						color = last_frame.get_dot(x,y)
				else:
					color = int((reduced.getpixel((x,y))/255.0)*15)
				frame.set_dot(x=x, y=y, value=color)
				
		frames += [frame]
		last_frame = frame
		
	return frames

def load_and_append_image(anim, filename):
	if not os.path.exists(filename):
		#print "Not found:", filename
		return False
	print "Appending ", filename
	src = Image.open(filename)
	last_filename = filename
	
	(w, h) = src.size
	if len(anim.frames) > 0 and (w != anim.width or h != anim.height):
		print "ERROR: Image sizes must be uniform!  Anim is %dx%d, image is %dx%d" % (w, h, anim.width, anim.height)
		sys.exit(1)
	
	(anim.width, anim.height) = (w, h)
	
	if filename.endswith('.gif'):
		anim.frames += gif_frames(src)
	else:
		alpha = None
		try:
			alpha = Image.fromstring('L', src.size, src.tostring('raw', 'A'))
		except:
			pass # No alpha channel available?
		
		reduced = src.convert("L")
		
		frame = procgame.dmd.Frame(w, h)
		
		for x in range(w):
			for y in range(h):
				color = int((reduced.getpixel((x,y))/255.0)*15)
				if alpha:
					color += int((alpha.getpixel((x,y))/255.0)*15) << 4
				frame.set_dot(x=x, y=y, value=color)
		
		anim.frames += [frame]
	
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
		anin.frames.append(frame)
	
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
	
	for filename in src_filenames:
		if filename.endswith('.txt'):
			load_and_append_text(anim=anim, filename=filename)
		else:
			load_and_append_image(anim=anim, filename=filename)
	
	if len(anim.frames) == 0:
		print "ERROR: No frames found!"
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
