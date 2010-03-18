import pinproc
import struct
import time
import os
import game

class Frame(pinproc.DMDBuffer):
	"""DMD frame/bitmap."""
	def __init__(self, width, height):
		super(Frame, self).__init__(width, height)
		self.width = width
		self.height = height

	def copy_rect(dst, dst_x, dst_y, src, src_x, src_y, width, height, op="copy"):
		if not (issubclass(type(dst), pinproc.DMDBuffer) and issubclass(type(src), pinproc.DMDBuffer)):
			raise ValueError, "Incorrect types"
		src.copy_to_rect(dst, dst_x, dst_y, src_x, src_y, width, height, op)
	copy_rect = staticmethod(copy_rect)
	
	def copy(self):
		frame = Frame(self.width, self.height)
		frame.set_data(self.get_data())
		return frame
	
	def ascii(self):
		output = ''
		table = [' ', '.', '.', '.', ',', ',', ',', '-', '-', '=', '=', '=', '*', '*', '#', '#',]
		for y in range(self.height):
			for x in range(self.width):
				dot = self.get_dot(x, y)
				output += table[dot]
			output += "\n"
		return output

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
		if self.width == None or self.height == None:
			raise ValueError, "width and height must be set on Animation before it can be saved."
		header = struct.pack("IIII", 0x00646D64, len(self.frames), self.width, self.height)
		if len(header) != 16:
			raise ValueError, "Packed size not 16 bytes as expected: %d" % (len(header))
		f = open(filename, 'w')
		f.write(header)
		for frame in self.frames:
			f.write(frame.get_data())
		f.close()

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


class Layer(object):
	"""
	Abstract layer object.  
	Provides a stream of frames through its next_frame() method.
	"""
	def __init__(self, opaque=False):
		"""
		Initialize a new Layer object.
		
		Keyword arguments:
		opaque -- Determines whether layers below this one will be rendered.
		          If True, the DisplayController will not render any layers
		          after this one (such as from Modes with lower priorities).
		"""
		super(Layer, self).__init__()
		self.opaque = opaque
		self.set_target_position(0, 0)
		self.target_x_offset = 0
		self.target_y_offset = 0
		self.enabled = True
		self.composite_op = 'copy'
		self.transition = None
	def set_target_position(self, x, y):
		"""Sets the location in the final output that this layer will be positioned at."""
		self.target_x = x
		self.target_y = y
	def next_frame(self):
		"""Returns an instance of a Frame object to be shown, or None if there is no frame."""
		return None
	def composite_next(self, target):
		"""Composites the next frame of this layer onto the given target buffer."""
		src = self.next_frame()
		if src != None:
			if self.transition != None:
				src = self.transition.next_frame(from_frame=target, to_frame=src)
			Frame.copy_rect(dst=target, dst_x=self.target_x+self.target_x_offset, dst_y=self.target_y+self.target_y_offset, src=src, src_x=0, src_y=0, width=src.width, height=src.height, op=self.composite_op)
		return src

class TransitionOutHelperMode(game.Mode):
	def __init__(self, game, priority, transition, layer):
		super(TransitionOutHelperMode, self).__init__(game=game, priority=priority)
		self.layer = layer
		self.layer.transition = transition
		self.layer.transition.in_out = 'out'
		self.layer.transition.completed_handler = self.transition_completed
	def mode_started(self):
		self.layer.transition.start()
	def transition_completed(self):
		self.game.modes.remove(self)

class LayerTransitionBase(object):
	"""Transition that """
	def __init__(self):
		super(LayerTransitionBase, self).__init__()
		self.progress = 0.0
		self.progress_per_frame = 1.0/60.0 # default to 60fps
		self.progress_mult = 0 # not moving, -1 for B to A, 1 for A to B
		self.completed_handler = None
		self.in_out = 'in'
	def start(self):
		self.reset()
		self.progress_mult = 1
	def pause(self):
		self.progress_mult = 0
	def reset(self):
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
	def __init__(self, opaque=False, frame=None):
		super(FrameLayer, self).__init__(opaque)
		self.frame = frame
	def next_frame(self):
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
			self.buffer.clear()
			layer.composite_next(self.buffer)
			return self.buffer
		else:
			return None
			

class GroupedLayer(Layer):
	"""docstring for GroupedLayer"""
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
	"""DisplayController, on update(), iterates over the game's mode and composites their layer member variable to the output."""
	def __init__(self, game, width=128, height=32, message_font=None):
		self.game = game
		self.message_layer = None
		self.width = width
		self.height = height
		self.capture = None
		if message_font != None:
			self.message_layer = TextLayer(width/2, height-2*7, message_font, "center")
		# Do two updates to get the pump primed:
		for x in range(2):
			self.update()
		
	def set_message(self, message, seconds):
		if self.message_layer == None:
			raise ValueError, "Message_font must be specified in constructor to enable message layer."
		self.message_layer.set_text(message, seconds)

	def update(self):
		"""Update the DMD."""
		layers = []
		for mode in self.game.modes.modes:
			if hasattr(mode, 'layer') and mode.layer != None:
				layers += [mode.layer]
		
		frame = Frame(self.width, self.height)
		for layer in layers[::-1]: # We reverse the list here so that the top layer gets the last say.
			if layer.enabled:
				layer.composite_next(frame)
		
		if self.message_layer != None:
			self.message_layer.composite_next(frame)
			
		if frame != None:
			self.game.proc.dmd_draw(frame)
			if self.capture != None:
				self.capture.append(frame)

