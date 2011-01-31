import Image
import procgame.dmd

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
	
	# Construct a lookup table from 0-255 to 0-15:
	eight_to_four_map = [0] * 256
	for l in range(256):
		eight_to_four_map[l] = 0xf0 + int(round((l/255.0) * 15.0))
	
	for src_im in ImageSequence(src):
		reduced = src.convert("L")
		
		frame = procgame.dmd.Frame(w, h)
		
		for x in range(w):
			for y in range(h):
				idx = src_im.getpixel((x, y)) # Get the palette index for this pixel
				if idx == background_idx:
					# background index means use the prior frame's dot data
					if last_frame:
						color = last_frame.get_dot(x,y)
					else:
						# No prior frame to refer to.
						color = 0xff # Don't have a good option here.
				elif idx == transparent_idx:
					color = 0x00
				else:
					color = eight_to_four_map[reduced.getpixel((x,y))]
				frame.set_dot(x=x, y=y, value=color)
		
		frames.append(frame)
		last_frame = frame
		
	return frames
