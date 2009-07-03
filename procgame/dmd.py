import struct
import time

class Frame(object):
	"""DMD frame/bitmap."""
	def __init__(self, width, height, data=None):
		super(Frame, self).__init__()
		self.width = width
		self.height = height
		if data == None:
			self.clear()
		else:
			self.data = data

	def clear(self):
		"""Set this frame to black."""
		self.data = []
		for x in range(self.width):
			self.data += [[0] * self.height]
		
	def set_dot(self, x, y, value):
		"""Assign the value for one pixel."""
		self.data[x][y] = value

	def get_dot(self, x, y):
		"""Returns the value of the specified pixel."""
		return self.data[x][y]
		
	def copy_rect(dst, dst_x, dst_y, src, src_x, src_y, width, height):
		"""Static method to copy a rectangle of a frame into another."""
		if dst_x < 0:
			src_x += -dst_x
			width -= -dst_x
			dst_x = 0
		if dst_y < 0:
			src_y += -dst_y
			height -= -dst_y
			dst_y = 0
		if src_x < 0:
			dst_x += -src_x
			width -= -src_x
			src_x = 0
		if src_y < 0:
			dst_y += -src_y
			height -= -src_y
			src_y = 0
		if src_x + width  > src.width:  width = src.width - src_x
		if src_y + height > src.height: height = src.height - src_y
		if dst_x + width  > dst.width:  width = dst.width - dst_x
		if dst_y + height > dst.height: height = dst.height - dst_y
		for x in xrange(0, width):
			for y in xrange(0, height):
				dst.set_dot(dst_x + x, dst_y + y, src.get_dot(src_x + x, src_y + y))
	copy_rect = staticmethod(copy_rect)

class Animation(object):
	"""A set of frames."""
	def __init__(self):
		super(Animation, self).__init__()
		self.width = None
		self.height = None
		self.frames = []
	def load(self, filename):
		"""Loads a series of frames from a .dmd (DMDAnimator) file.
		
		File format is as follows:
		
		  4 bytes - header data (unused)
		  4 bytes - frame_count
		  4 bytes - width of animation frames in pixels
		  4 bytes - height of animation frames in pixels
		  ? bytes - Frames: frame_count * width * height bytes
		
		Frame data is laid out row0..rowN.  Byte values of each pixel
		are 00-03, 00 being black and 03 being brightest.  This is
		subject to change to allow for more brightness levels and/or
		transparency.
		"""
		self.frames = []
		f = open(filename, 'r')
		f.seek(4)
		frame_count = struct.unpack("I", f.read(4))[0]
		self.width = struct.unpack("I", f.read(4))[0]
		self.height = struct.unpack("I", f.read(4))[0]
		print(frame_count, self.width, self.height)
		for frame_index in range(frame_count):
			str_frame = f.read(self.width * self.height)
			new_frame = Frame(self.width, self.height) #, map(lambda x: ord(x), str_frame))
			for i in range(len(str_frame)):
				new_frame.set_dot(i % self.width, i / self.width, ord(str_frame[i]))
			self.frames += [new_frame]

class Font(object):
	"""A DMD bitmap font."""
	def __init__(self, filename=None):
		super(Font, self).__init__()
		self.__anim = Animation()
		self.char_size = None
		self.bitmap = None
		self.char_widths = None
		if filename != None:
			self.load(filename)
		
	def load(self, filename):
		"""Loads the font from a .dmd file (see Animation.load()).
		Fonts are stored in .dmd files with frame 0 containing the bitmap data
		and frame 1 containing the character widths.  96 characters (32..127,
		ASCII printables) are stored in a 10x10 grid, starting with space ' ' 
		in the upper left.
		"""
		self.__anim.load(filename)
		if self.__anim.width != self.__anim.height:
			raise ValueError, "Width != height!"
		if len(self.__anim.frames) != 2:
			raise ValueError, "Expected 2 frames: %d" % (len(self.__anim.frames))
		self.char_size = self.__anim.width / 10
		self.bitmap = self.__anim.frames[0]
		self.char_widths = []
		for i in range(96):
			self.char_widths += [self.__anim.frames[1].get_dot(i%self.__anim.width, i/self.__anim.width)]
		
	def draw(self, frame, text, x, y):
		"""Uses this font's characters to draw the given string at the given position."""
		for ch in text:
			char_offset = ord(ch) - ord(' ')
			if char_offset < 0 or char_offset >= 96:
				continue
			char_x = self.char_size * (char_offset % 10)
			char_y = self.char_size * (char_offset / 10)
			width = self.char_widths[char_offset]
			Frame.copy_rect(dst=frame, dst_x=x, dst_y=y, src=self.bitmap, src_x=char_x, src_y=char_y, width=width, height=self.char_size)
			x += width
		return x
	
	def size(self, text):
		"""Returns a tuple of the width and height of this text as rendered with this font."""
		x = 0
		for ch in text:
			char_offset = ord(ch) - ord(' ')
			if char_offset < 0 or char_offset >= 96:
				continue
			width = self.char_widths[char_offset]
			x += width
		return (x, self.char_size)


class Layer(object):
	"""Collection of frames displayed sequentially, as an animation.  Optionally holds the last frame on-screen."""
	def __init__(self, opaque=False):
		super(Layer, self).__init__()
		self.opaque = opaque
		self.set_target_position(0, 0)
		self.target_x_offset = 0
		self.target_y_offset = 0
		self.enabled = True
	def set_target_position(self, x, y):
		"""Sets the location in the final output that this layer will be positioned at."""
		self.target_x = x
		self.target_y = y
	def next_frame(self):
		"""Returns the frame to be shown, or None if there is no frame."""
		return None
	def composite_next(self, target):
		"""Composites the next frame of this layer onto the given target buffer."""
		src = self.next_frame()
		if src != None:
			Frame.copy_rect(dst=target, dst_x=self.target_x+self.target_x_offset, dst_y=self.target_y+self.target_y_offset, src=src, src_x=0, src_y=0, width=src.width, height=src.height)

class AnimatedLayer(Layer):
	"""Collection of frames displayed sequentially, as an animation.  Optionally holds the last frame on-screen."""
	def __init__(self, opaque=False, hold=True, frames=[]):
		super(AnimatedLayer, self).__init__(opaque)
		self.hold = hold
		self.frames = frames
	def next_frame(self):
		"""Returns the frame to be shown, or None if there is no frame."""
		if len(self.frames) == 0:
			return None
		frame = self.frames[0] # Get the first frame in this layer's list.
		if self.hold == False or len(self.frames) > 1:
			del self.frames[0] # Pop off the frame if there are others
		return frame

class TextLayer(Layer):
	"""Layer that displays text."""
	def __init__(self, x, y, font, justify="left", opaque=False):
		super(TextLayer, self).__init__(opaque)
		self.set_target_position(x, y)
		self.font = font
		self.started_at = None
		self.seconds = None # Number of seconds to show the text for
		self.frame = None # Frame that text is rendered into.
		self.justify = justify
		
	def set_text(self, text, seconds=None):
		"""Displays the given message for the given number of seconds."""
		self.started_at = None
		self.seconds = seconds
		if text == None:
			self.frame = None
		else:
			(w, h) = self.font.size(text)
			self.frame = Frame(w, h)
			self.font.draw(self.frame, text, 0, 0)
			if self.justify == "left":
				(self.target_x_offset, self.target_y_offset) = (0,0)
			elif self.justify == "right":
				(self.target_x_offset, self.target_y_offset) = (-w,0)
			elif self.justify == "center":
				(self.target_x_offset, self.target_y_offset) = (-w/2,0)

	def next_frame(self):
		if self.started_at == None:
			self.started_at = time.time()
		if (self.seconds != None) and ((self.started_at + self.seconds) < time.time()):
			self.frame = None
		return self.frame

class ScriptedLayer(Layer):
	"""Displays a set of layers based on a simple script (dictionary)."""
	def __init__(self, width, height, script):
		super(ScriptedLayer, self).__init__()
		self.buffer = Frame(width, height)
		self.script = script
		self.script_index = 0
		self.frame_start_time = None
	
	def next_frame(self):
		# This assumes looping.  TODO: Add code to not loop!
		if self.frame_start_time == None:
			self.frame_start_time = time.time()
		script_item = self.script[self.script_index]
		time_on_frame = time.time() - self.frame_start_time
		if time_on_frame > script_item['seconds']:
			# Time for the next frame:
			self.script_index += 1
			if self.script_index == len(self.script):
				self.script_index = 0
			script_item = self.script[self.script_index]
			self.frame_start_time = time.time()
		layer = script_item['layer']
		if layer != None:
			#return layer.next_frame()
			self.buffer.clear()
			layer.composite_next(self.buffer)
			return self.buffer
		else:
			return None
			

class GroupedLayer(Layer):
	"""docstring for GroupedLayer"""
	def __init__(self, width, height, layers=[]):
		super(GroupedLayer, self).__init__()
		self.buffer = Frame(width, height)
		self.layers = layers

	def next_frame(self):
		self.buffer.clear()
		for layer in self.layers:
			if layer.enabled:
				layer.composite_next(self.buffer)
			if layer.opaque:
				break
		return self.buffer


class DisplayController(GroupedLayer):
	"""docstring for DisplayController"""
	def __init__(self, proc, width=128, height=32):
		super(DisplayController, self).__init__(width, height)
		self.proc = proc

	def update(self):
		"""Update the DMD."""
		frame = self.next_frame()
		if frame != None:
			f = ""
			for y in range(frame.height):
				for x in range(frame.width):
					f += chr(frame.data[x][y]*60)*4
			self.proc.dmd_draw(f)

