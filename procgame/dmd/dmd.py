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
				output += table[dot]
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


class MarkupFrameGenerator:
	"""Renders a :class:`~procgame.dmd.Frame` for given text-based markup.

		The markup format presently uses three markup tokens: 
		``#`` (for headlines) and ``[`` and ``]`` for plain text.  The markup tokens
		indicate justification.  Lines with no markup or a leading ``#`` or ``[``
		will be left-justified.  Lines with a trailing ``#`` or ``]`` will be right-
		justified.  Lines with both will be centered.

		The width and min_height are specified with instantiation.

		Fonts can be adjusted by assigning the :attr:`font_plain` and :attr:`font_bold` member variables.
		"""
	
	font_plain = None
	"""Font used for plain, non-bold characters."""
	font_bold = None
	""""""
	
	def __init__(self, width=128, min_height=32):
		self.width = width
		self.min_height = min_height
		self.frame = None
		self.font_plain = font_named('Font07x5.dmd')
		self.font_bold = font_named('Font09Bx7.dmd')
	def frame_for_markup(self, markup):
		"""Returns a Frame with the given markup rendered within it.
			The frame width is fixed, but the height will be adjusted
			to fit the contents while respecting min_height."""
		lines = markup.split('\n')
		for draw in [False, True]:
			y = 0
			for line in lines:
				if line.startswith('#') and line.endswith('#'): # centered headline!
					y = self.__draw_text(y=y, text=line[1:-1], font=self.font_bold, justify='center', draw=draw)
				elif line.startswith('#'): # left-justified headline
					y = self.__draw_text(y=y, text=line[1:], font=self.font_bold, justify='left', draw=draw)
				elif line.endswith('#'): # right-justified headline
					y = self.__draw_text(y=y, text=line[:-1], font=self.font_bold, justify='right', draw=draw)
				elif line.startswith('[') and line.endswith(']'): # centered text
					y = self.__draw_text(y=y, text=line[1:-1], font=self.font_plain, justify='center', draw=draw)
				elif line.endswith(']'): # right-justified text
					y = self.__draw_text(y=y, text=line[:-1], font=self.font_plain, justify='right', draw=draw)
				elif line.startswith('['): # left-justified text
					y = self.__draw_text(y=y, text=line[1:], font=self.font_plain, justify='left', draw=draw)
				else: # left-justified but nothing to clip off
					y = self.__draw_text(y=y, text=line, font=self.font_plain, justify='left', draw=draw)
			if not draw: # this was a test run to get the height
				self.frame = Frame(width=self.width, height=max(self.min_height, y))
		return self.frame

	def __draw_text(self, y, text, font, justify, draw):
		if max(font.char_widths) * len(text) > self.width:
			# Need to do word-wrapping!
			line = ''
			w = 0
			for ch in text:
				line += ch
				w += font.size(ch)[0]
				if w > self.width:
					# Too much! We need to back-track for the last space, if possible..
					idx = line.rfind(' ')
					if idx == -1:
						# No space; we'll have to break before this char and continue.
						y = self.__draw_line(y=y, text=line[:-1], font=font, justify=justify, draw=draw)
						line = ch
					else:
						# We have found a space!
						y = self.__draw_line(y=y, text=line[:idx], font=font, justify=justify, draw=draw)
						line = line[idx+1:]
					# Recalculate w.
					w = font.size(line)[0]
			if len(line) > 0: # leftover text we need to draw
				y = self.__draw_line(y=y, text=line, font=font, justify=justify, draw=draw)
			return y
		else:
			return self.__draw_line(y=y, text=text, font=font, justify=justify, draw=draw)
	def __draw_line(self, y, text, font, justify, draw):
		"""Draw a line without concern for word-wrapping."""
		if draw:
			x = 0 # TODO: x should be set based on 'justify'.
			if justify != 'left':
				w = font.size(text)[0]
				if justify == 'center':
					x = (self.frame.width - w)/2
				else:
					x = (self.frame.width - w)
			font.draw(frame=self.frame, text=text, x=x, y=y)
		y += font.char_size
		return y




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

class LayerTransitionBase(object):
	"""Transition base class."""

	progress = 0.0
	"""Transition progress from 0.0 (100% from frame, 0% to frame) to 1.0 (0% from frame, 100% to frame).
	Updated by :meth:`next_frame`."""
	
	progress_per_frame = 1.0/60.0
	"""Progress increment for each frame.  Defaults to 1/60, or 60fps."""
	
	progress_mult = 0 # not moving, -1 for B to A, 1 for A to B .... not documented as play/pause manipulates.
	
	completed_handler = None
	"""Function to be called once the transition has completed."""
	
	in_out = 'in'
	"""If ``'in'`` the transition is moving from `from` to `to`; if ``'out'`` the transition is moving
	from `to` to `from`."""

	def __init__(self):
		super(LayerTransitionBase, self).__init__()
	
	def start(self):
		"""Start the transition."""
		self.reset()
		self.progress_mult = 1
	def pause(self):
		"""Pauses the transition at the current position."""
		self.progress_mult = 0
	def reset(self):
		"""Reset the transition to the beginning."""
		self.progress_mult = 0
		self.progress = 0
	def next_frame(self, from_frame, to_frame):
		"""Applies the transition and increments the progress if the transition is running.  Returns the resulting frame."""
		self.progress = max(0.0, min(1.0, self.progress + self.progress_mult * self.progress_per_frame))
		if self.progress <= 0.0:
			if self.in_out == 'in':
				return from_frame
			else:
				return to_frame
		if self.progress >= 1.0:
			if self.completed_handler != None:
				self.completed_handler()
			if self.in_out == 'in':
				return to_frame
			else:
				return from_frame
		return self.transition_frame(from_frame=from_frame, to_frame=to_frame)
	def transition_frame(self, from_frame, to_frame):
		"""Applies the transition at the current progress value.
		   Subclasses should override this method to provide more interesting transition effects.
		   Base implementation simply returns the from_frame."""
		return from_frame

class ExpandTransition(LayerTransitionBase):
	def __init__(self, direction='vertical'):
		super(ExpandTransition, self).__init__()
		self.direction = direction
		self.progress_per_frame = 1.0/11.0
	def transition_frame(self, from_frame, to_frame):
		frame = Frame(width=from_frame.width, height=from_frame.height)
		dst_x, dst_y = 0, 0
		prog = self.progress
		if self.in_out == 'out':
			prog = 1.0 - prog
		dst_x, dst_y = {
		 'vertical': (0, frame.height/2-prog*(frame.height/2)),
		 'horizontal':  (frame.width/2-prog*(frame.width/2), 0),
		}[self.direction]

		if (self.direction == 'vertical'):
                	width = frame.width
			height = prog*frame.height
		else:
			width = prog*frame.width
			height = frame.height

		Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=dst_x, src_y=dst_y, width=width, height=height, op='copy')
		return frame

class SlideOverLayerTransition(LayerTransitionBase):
	def __init__(self, direction='north'):
		super(SlideOverLayerTransition, self).__init__()
		self.direction = direction
		self.progress_per_frame = 1.0/15.0
	def transition_frame(self, from_frame, to_frame):
		frame = from_frame.copy()
		dst_x, dst_y = 0, 0
		prog = self.progress
		if self.in_out == 'in':
			prog = 1.0 - prog
		dst_x, dst_y = {
		 'north': (0, -prog*frame.height),
		 'south': (0,  prog*frame.height),
		 'east':  (-prog*frame.width, 0),
		 'west':  ( prog*frame.width, 0),
		}[self.direction]
		Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
		return frame

class PushLayerTransition(LayerTransitionBase):
	def __init__(self, direction='north'):
		super(PushLayerTransition, self).__init__()
		self.direction = direction
		self.progress_per_frame = 1.0/15.0
	def transition_frame(self, from_frame, to_frame):
		frame = Frame(width=from_frame.width, height=from_frame.height)
		dst_x, dst_y = 0, 0
		prog = self.progress
		prog1 = self.progress
		if self.in_out == 'in':
			prog = 1.0 - prog
		else:
			prog1 = 1.0 - prog1
		dst_x, dst_y, dst_x1, dst_y1 = {
		 'north': (0, -prog*frame.height,  0,  prog1*frame.height),
		 'south': (0,  prog*frame.height,  0, -prog1*frame.height),
		 'east':  (-prog*frame.width, 0,    prog1*frame.width, 0),
		 'west':  ( prog*frame.width, 0,   -prog1*frame.width, 0),
		}[self.direction]
		Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
		Frame.copy_rect(dst=frame, dst_x=dst_x1, dst_y=dst_y1, src=from_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
		return frame

class CrossFadeTransition(LayerTransitionBase):
	"""Performs a cross-fade between two layers.  As one fades out the other one fades in."""
	def __init__(self, width, height):
		LayerTransitionBase.__init__(self)
		self.width, self.height = width, height
		self.progress_per_frame = 1.0/45.0
		# Create the frames that will be used in the composite operations:
		self.frames = []
		for value in range(16):
			frame = Frame(width, height)
			frame.fill_rect(0, 0, width, height, value)
			self.frames.append(frame)
	def transition_frame(self, from_frame, to_frame):
		# Calculate the frame index:
		if self.in_out == 'in':
			index = int(self.progress * (len(self.frames)-1))
		else:
			index = int((1.0-self.progress) * (len(self.frames)-1))
		# Subtract the respective reference frame from each of the input frames:
		from_frame = from_frame.copy()
		Frame.copy_rect(dst=from_frame, dst_x=0, dst_y=0, src=self.frames[index], src_x=0, src_y=0, width=self.width, height=self.height, op='sub')
		to_frame = to_frame.copy()
		Frame.copy_rect(dst=to_frame, dst_x=0, dst_y=0, src=self.frames[-(1+index)], src_x=0, src_y=0, width=self.width, height=self.height, op='sub')
		# Add the results together:
		Frame.copy_rect(dst=from_frame, dst_x=0, dst_y=0, src=to_frame, src_x=0, src_y=0, width=self.width, height=self.height, op='add')
		return from_frame

class FrameLayer(Layer):
	"""Displays a single frame."""
	
	blink_frames = None # Number of frame times to turn frame on/off
	blink_frames_counter = 0
	frame_old = None
	
	def __init__(self, opaque=False, frame=None):
		super(FrameLayer, self).__init__(opaque)
		self.frame = frame
	def next_frame(self):
		if self.blink_frames > 0:
			if self.blink_frames_counter == 0:
				self.blink_frames_counter = self.blink_frames
				if self.frame == None:
					self.frame = self.frame_old
				else:
					self.frame_old = self.frame
					self.frame = None
			else:
				self.blink_frames_counter -= 1
		return self.frame

class AnimatedLayer(Layer):
	"""Collection of frames displayed sequentially, as an animation.  Optionally holds the last frame on-screen."""
	def __init__(self, opaque=False, hold=True, repeat=False, frame_time=1, frames=None):
		super(AnimatedLayer, self).__init__(opaque)
		self.hold = hold
		self.repeat = repeat
		if frames == None:
			self.frames = list()
		else:
			self.frames = frames
		self.frame_time = frame_time # Number of frames each frame should be displayed for before moving to the next.
		self.frame_time_counter = self.frame_time
	def next_frame(self):
		"""Returns the frame to be shown, or None if there is no frame."""
		if len(self.frames) == 0:
			return None
		frame = self.frames[0] # Get the first frame in this layer's list.
		self.frame_time_counter -= 1
		if (self.hold == False or len(self.frames) > 1) and (self.frame_time_counter == 0):
			if self.repeat:
				f = self.frames[0]
				del self.frames[0]
				self.frames += [f]
			else:
				del self.frames[0] # Pop off the frame if there are others
		if self.frame_time_counter == 0:
			self.frame_time_counter = self.frame_time
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
		self.frame_old = None
		self.justify = justify
		self.blink_frames = None # Number of frame times to turn frame on/off
		self.blink_frames_counter = 0
		
	def set_text(self, text, seconds=None, blink_frames=None):
		"""Displays the given message for the given number of seconds."""
		self.started_at = None
		self.seconds = seconds
		self.blink_frames = blink_frames
		self.blink_frames_counter = self.blink_frames
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
		return self

	def next_frame(self):
		if self.started_at == None:
			self.started_at = time.time()
		if (self.seconds != None) and ((self.started_at + self.seconds) < time.time()):
			self.frame = None
		elif self.blink_frames > 0:
			if self.blink_frames_counter == 0:
				self.blink_frames_counter = self.blink_frames
				if self.frame == None:
					self.frame = self.frame_old
				else:
					self.frame_old = self.frame
					self.frame = None
			else:
				self.blink_frames_counter -= 1
		return self.frame
	
	def is_visible(self):
		return self.frame != None

class ScriptedLayer(Layer):
	"""Displays a set of layers based on a simple script.
	
	**Script Format**
	
	The script is an list of dictionaries.  Each dictionary contains two keys: ``seconds`` and
	``layer``.  ``seconds`` is the number of seconds that ``layer`` will be displayed before 
	advancing to the next script element.
	
	If ``layer`` is ``None``, no frame will be returned by this layer for the duration of that script
	element.
	
	Example script::
	
	  [{'seconds':3.0, 'layer':self.game_over_layer}, {'seconds':3.0, 'layer':None}]
	
	"""
	def __init__(self, width, height, script):
		super(ScriptedLayer, self).__init__()
		self.buffer = Frame(width, height)
		self.script = script
		self.script_index = 0
		self.frame_start_time = None
		self.force_direction = None
		self.on_complete = None
	
	def next_frame(self):
		# This assumes looping.  TODO: Add code to not loop!
		if self.frame_start_time == None:
			self.frame_start_time = time.time()
		script_item = self.script[self.script_index]
		time_on_frame = time.time() - self.frame_start_time
		if self.force_direction != None or time_on_frame > script_item['seconds']:
			if self.force_direction == False:
				self.script_index -= 1
			else:
				self.script_index += 1

			# Only force one item.
			self.force_direction = None

			if self.script_index == len(self.script):
				self.script_index = 0
				if self.on_complete != None:
					self.on_complete()
			script_item = self.script[self.script_index]
			self.frame_start_time = time.time()
		layer = script_item['layer']
		if layer != None:
			self.buffer.clear()
			layer.composite_next(self.buffer)
			return self.buffer
		else:
			return None

	def force_next(self, forward=True):
		"""Advances to the next script element in the given direction."""
		self.force_direction = forward
			

class GroupedLayer(Layer):
	""":class:`.Layer` subclass that composites several sublayers (members of its :attr:`layers` list attribute) together."""
	
	layers = None
	"""List of layers to be composited together whenever this layer's :meth:`~Layer.next_frame` is called.
	
	Layers are composited first to last using each layer's
	:meth:`~procgame.dmd.Layer.composite_next` method.  Compositing is ended after a layer that returns
	non-``None`` from :meth:`~Layer.composite_next` is :attr:`~Layer.opaque`."""
	
	def __init__(self, width, height, layers=None):
		super(GroupedLayer, self).__init__()
		self.buffer = Frame(width, height)
		if layers == None:
			self.layers = list()
		else:
			self.layers = layers

	def next_frame(self):
		self.buffer.clear()
		composited_count = 0
		for layer in self.layers:
			frame = None
			if layer.enabled:
				frame = layer.composite_next(self.buffer)
			if frame != None:
				composited_count += 1
			if frame != None and layer.opaque: # If an opaque layer doesn't draw anything, don't stop.
				break
		if composited_count == 0:
			return None
		return self.buffer

class DisplayController:
	"""Manages the process of obtaining DMD frames from active modes and compositing them together for
	display on the DMD.
	
	**Using DisplayController**
	
	1. Add a :class:`DisplayController` instance to your :class:`~procgame.game.GameController` subclass::
	
	    class Game(game.GameController):
	      def __init__(self, machineType):
	        super(Game, self).__init__(machineType)
	        self.dmd = dmd.DisplayController(self, width=128, height=32,
	                                         message_font=font_tiny7)
	
	2. In your subclass's :meth:`~procgame.game.GameController.dmd_event` call :meth:`DisplayController.update`::
	
	    def dmd_event(self):
	        self.dmd.update()
	
	"""
	
	frame_handlers = []
	"""If set, frames obtained by :meth:`.update` will be sent to the functions
	in this list with the frame as the only parameter.
	
	This list is initialized to contain only ``self.game.proc.dmd_draw``."""
	
	def __init__(self, game, width=128, height=32, message_font=None):
		self.game = game
		self.message_layer = None
		self.width = width
		self.height = height
		if message_font != None:
			self.message_layer = TextLayer(width/2, height-2*7, message_font, "center")
		# Do two updates to get the pump primed:
		for x in range(2):
			self.update()
		self.frame_handlers.append(self.game.proc.dmd_draw)
		
	def set_message(self, message, seconds):
		if self.message_layer == None:
			raise ValueError, "Message_font must be specified in constructor to enable message layer."
		self.message_layer.set_text(message, seconds)

	def update(self):
		"""Iterates over :attr:`procgame.game.GameController.modes` from lowest to highest
		and composites a DMD image for this
		point in time by checking for a ``layer`` attribute on each :class:`~procgame.game.Mode`.
		If the mode has a layer attribute, that layer's :meth:`~procgame.dmd.Layer.composite_next` method is called
		to apply that layer's next frame to the frame in progress."""
		layers = []
		for mode in self.game.modes.modes:
			if hasattr(mode, 'layer') and mode.layer != None:
				layers.append(mode.layer)
				if mode.layer.opaque:
					break # if we have an opaque layer we don't render any lower layers
		
		frame = Frame(self.width, self.height)
		for layer in layers[::-1]: # We reverse the list here so that the top layer gets the last say.
			if layer.enabled:
				layer.composite_next(frame)
		
		if self.message_layer != None:
			self.message_layer.composite_next(frame)
			
		if frame != None:
			for handler in self.frame_handlers:
				handler(frame)

