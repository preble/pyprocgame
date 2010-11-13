import pinproc
import struct
import time
import os
from .. import config
from .. import util

class Frame(pinproc.DMDBuffer):
	"""DMD frame/bitmap.
	
	Subclass of :class:`pinproc.DMDBuffer`.
	"""
	
	width = 0
	"""Width of the frame in dots."""
	height = 0
	"""Height of the frame in dots."""
	
	def __init__(self, width, height):
		"""Initializes the frame to the given `width` and `height`."""
		super(Frame, self).__init__(width, height)
		self.width = width
		self.height = height

	def copy_rect(dst, dst_x, dst_y, src, src_x, src_y, width, height, op="copy"):
		"""Static method which performs some type checking before calling :meth:`pinproc.DMDBuffer.copy_to_rect`."""
		if not (issubclass(type(dst), pinproc.DMDBuffer) and issubclass(type(src), pinproc.DMDBuffer)):
			raise ValueError, "Incorrect types"
		src.copy_to_rect(dst, dst_x, dst_y, src_x, src_y, width, height, op)
	copy_rect = staticmethod(copy_rect)
	
	def subframe(self, x, y, width, height):
		"""Generates a new frame based on a sub rectangle of this frame."""
		subframe = Frame(width, height)
		Frame.copy_rect(subframe, 0, 0, self, x, y, width, height, 'copy')
		return subframe
	
	def copy(self):
		"""Returns a copy of itself."""
		frame = Frame(self.width, self.height)
		frame.set_data(self.get_data())
		return frame
	
	def ascii(self):
		"""Returns an ASCII representation of itself."""
		output = ''
		table = [' ', '.', '.', '.', ',', ',', ',', '-', '-', '=', '=', '=', '*', '*', '#', '#',]
		for y in range(self.height):
			for x in range(self.width):
				dot = self.get_dot(x, y)
				output += table[dot & 0xf]
			output += "\n"
		return output
	
	def create_with_text(lines, palette = {' ':0, '*':15}):
		"""Create a frame based on text.
		
		This class method can be used to generate small sprites within the game's source code::
		
			frame = Frame.create_with_text(lines=[ \\
			    '*+++*', \\
			    ' *+* ', \\
			    '  *  '], palette={' ':0, '+':7, '*':15})
		"""
		height = len(lines)
		if height > 0:
			width = len(lines[0])
		else:
			width = 0
		frame = Frame(width, height)
		for y in range(height):
			for x in range(width):
				char = lines[y][x]
				frame.set_dot(x, y, palette[char])
		return frame
	create_with_text = staticmethod(create_with_text)

	def create_frames_from_grid( self, num_cols, num_rows ):
		frames = []
		width = self.width / num_cols
		height = self.height / num_rows
	
		# Use nested loops to step through each column of each row, creating a new frame at each iteration and copying in the appropriate data.
		for row_index in range(0,num_rows):
			for col_index in range(0,num_cols):
				new_frame = Frame(width, height)
				Frame.copy_rect(dst=new_frame, dst_x=0, dst_y=0, src=self, src_x=width*col_index, src_y=height*row_index, width=width, height=height, op='copy')
				frames += [new_frame]
		return frames


class Animation(object):
	"""An ordered collection of :class:`~procgame.dmd.Frame` objects."""
	
	width = None
	"""Width of each of the animation frames in dots."""
	height = None
	"""Height of each of the animation frames in dots."""
	frames = []
	"""Ordered collection of :class:`~procgame.dmd.Frame` objects."""
	
	def __init__(self):
		"""Initializes the animation."""
		super(Animation, self).__init__()

	def load(self, filename):
		"""Loads a series of frames from a .dmd (DMDAnimator) file.
		
		File format is as follows: ::
		
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
		f = open(filename, 'rb')
		f.seek(4)
		frame_count = struct.unpack("I", f.read(4))[0]
		self.width = struct.unpack("I", f.read(4))[0]
		self.height = struct.unpack("I", f.read(4))[0]
		if os.path.getsize(filename) != 16 + self.width * self.height * frame_count:
			raise ValueError, "File size inconsistent with header information.  Old or incompatible file format?"
		for frame_index in range(frame_count):
			str_frame = f.read(self.width * self.height)
			new_frame = Frame(self.width, self.height)
			new_frame.set_data(str_frame)
			self.frames += [new_frame]
		return self

	def save(self, filename):
		"""Saves the animation as a .dmd file at the given location, `filename`."""
		if self.width == None or self.height == None:
			raise ValueError, "width and height must be set on Animation before it can be saved."
		header = struct.pack("IIII", 0x00646D64, len(self.frames), self.width, self.height)
		if len(header) != 16:
			raise ValueError, "Packed size not 16 bytes as expected: %d" % (len(header))
		f = open(filename, 'wb')
		f.write(header)
		for frame in self.frames:
			f.write(frame.get_data())
		f.close()

class Font(object):
	"""Variable-width bitmap font.
	
	Fonts can be loaded manually, using :meth:`load`, or with the :func:`font_named` utility function
	which supports searching a font path."""
	def __init__(self, filename=None):
		super(Font, self).__init__()
		self.__anim = Animation()
		self.char_size = None
		self.bitmap = None
		self.char_widths = None
		if filename != None:
			self.load(filename)
		
	def load(self, filename):
		"""Loads the font from a ``.dmd`` file (see :meth:`Animation.load`).
		Fonts are stored in .dmd files with frame 0 containing the bitmap data
		and frame 1 containing the character widths.  96 characters (32..127,
		ASCII printables) are stored in a 10x10 grid, starting with space (``' '``) 
		in the upper left at 0, 0.  The character widths are stored in the second frame
		within the 'raw' bitmap data in bytes 0-95.
		"""
		self.__anim.load(filename)
		if self.__anim.width != self.__anim.height:
			raise ValueError, "Width != height!"
		if len(self.__anim.frames) == 1:
			# We allow 1 frame for handmade fonts.
			# This is so that they can be loaded as a basic bitmap, have their char widths modified, and then be saved.
			print "Font animation file %s has 1 frame; adding one" % (filename)
			self.__anim.frames += [Frame(self.__anim.width, self.__anim.height)]
		elif len(self.__anim.frames) != 2:
			raise ValueError, "Expected 2 frames: %d" % (len(self.__anim.frames))
		self.char_size = self.__anim.width / 10
		self.bitmap = self.__anim.frames[0]
		self.char_widths = []
		for i in range(96):
			self.char_widths += [self.__anim.frames[1].get_dot(i%self.__anim.width, i/self.__anim.width)]
		return self
	
	def save(self, filename):
		"""Save the font to the given path."""
		out = Animation()
		out.width = self.__anim.width
		out.height = self.__anim.height
		out.frames = [self.bitmap, Frame(out.width, out.height)]
		for i in range(96):
			out.frames[1].set_dot(i%self.__anim.width, i/self.__anim.width, self.char_widths[i])
		out.save(filename)
		
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


font_path = []
"""Array of paths that will be searched by :meth:`~procgame.dmd.font_named` to locate fonts.

When this module is initialized the pyprocgame global configuration (:attr:`procgame.config.values`)
``font_path`` key path is used to initialize this array."""

def init_font_path():
    global font_path
    try:
        value = config.value_for_key_path('font_path')
        if issubclass(type(value), list):
            font_path.extend(map(os.path.expanduser, value))
        elif issubclass(type(value), str):
            font_path.append(os.path.expanduser(value))
        else:
            raise Exception, 'Expected string or array for font_path.'
    except ValueError, e:
        #print e
        pass

init_font_path()


__font_cache = {}
def font_named(name):
	"""Searches the :attr:`font_path` for a font file of the given name and returns an instance of :class:`Font` if it exists."""
	if name in __font_cache:
		return __font_cache[name]
	path = util.find_file_in_path(name, font_path)
	if path:
		import dmd # have to do this to get dmd.Font to work below... odd.
		font = dmd.Font(path)
		__font_cache[name] = font
		return font
	else:
		raise ValueError, 'Font named "%s" not found; font_path=%s.  Have you configured font_path in config.yaml?' % (name, font_path)


class Layer(object):
	"""
	The ``Layer`` class is the basis for the pyprocgame display architecture.
	Subclasses override :meth:`next_frame` to provide a frame for the current moment in time.
	Handles compositing of provided frames and applying transitions within a :class:`DisplayController` context.
	"""
	
	opaque = False
	"""Determines whether layers below this one will be rendered.  
	If `True`, the :class:`DisplayController` will not render any layers after this one 
	(such as from modes with lower priorities -- see :class:`DisplayController` for more information).
	"""
	
	target_x = 0
	"""Base `x` component of the coordinates at which this layer will be composited upon a target buffer."""
	target_y = 0
	"""Base `y` component of the coordinates at which this layer will be composited upon a target buffer."""
	target_x_offset = 0
	"""Translation component used in addition to :attr:`target_x` as this layer's final compositing position."""
	target_y_offset = 0
	"""Translation component used in addition to :attr:`target_y` as this layer's final compositing position."""
	enabled = True
	"""If `False`, :class:`DisplayController` will ignore this layer."""
	composite_op = 'copy'
	"""Composite operation used by :meth:`composite_next` when calling :meth:`~pinproc.DMDBuffer.copy_rect`."""
	transition = None
	"""Transition which :meth:`composite_next` applies to the result of :meth:`next_frame` prior to compositing upon the output."""
	
	def __init__(self, opaque=False):
		"""Initialize a new Layer object."""
		super(Layer, self).__init__()
		self.opaque = opaque
		self.set_target_position(0, 0)

	def reset(self):
		# To be overridden
		pass

	def set_target_position(self, x, y):
		"""Setter for :attr:`target_x` and :attr:`target_y`."""
		self.target_x = x
		self.target_y = y
	def next_frame(self):
		"""Returns an instance of a Frame object to be shown, or None if there is no frame.
		The default implementation returns ``None``; subclasses should implement this method."""
		return None
	def composite_next(self, target):
		"""Composites the next frame of this layer onto the given target buffer.
		Called by :meth:`DisplayController.update`.
		Generally subclasses should not override this method; implementing :meth:`next_frame` is recommended instead.
		"""
		src = self.next_frame()
		if src != None:
			if self.transition != None:
				src = self.transition.next_frame(from_frame=target, to_frame=src)
			Frame.copy_rect(dst=target, dst_x=self.target_x+self.target_x_offset, dst_y=self.target_y+self.target_y_offset, src=src, src_x=0, src_y=0, width=src.width, height=src.height, op=self.composite_op)
		return src

