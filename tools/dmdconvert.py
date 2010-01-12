import sys
import os
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import procgame.dmd
import time
#import pygame.image
import Image

def image_to_dmd(src_filename, dst_filename):
	"""docstring for image_to_dmd"""
	src = Image.open(src_filename)
	(w, h) = src.size
	
	reduced = src.convert("L") #.quantize(palette=pal_im).convert("P", palette=Image.ADAPTIVE, colors=4)#
	
	frame = procgame.dmd.Frame(w, h)
	
	for x in range(w):
		for y in range(h):
			color = int((reduced.getpixel((x,y))/255.0)*15)
			frame.set_dot(x=x, y=y, value=color+0x10)
	
	anim = procgame.dmd.Animation()
	(anim.width, anim.height) = (w, h)
	anim.frames = [frame]
	anim.save(dst_filename)

def main():
	if len(sys.argv) < 3:
		print("Usage: %s <image.png> <output.dmd>"%(sys.argv[0]))
		return
	image_to_dmd(src_filename=sys.argv[1], dst_filename=sys.argv[2])


if __name__ == "__main__":
	main()