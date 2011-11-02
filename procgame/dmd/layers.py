from dmd import *

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
	
	hold = True
	"""``True`` if the last frame of the animation should be held on-screen indefinitely."""
	
	repeat = False
	"""``True`` if the animation should be repeated indefinitely."""
	
	frame_time = 1
	"""Number of frame times each frame should be shown on screen before advancing to the next frame.  The default is 1."""
	
	frame_pointer = 0
	"""Index of the next frame to display.  Incremented by :meth:`next_frame`."""
	
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
		
		self.frame_listeners = []
		
		self.reset()
	
	def reset(self):
		"""Resets the animation back to the first frame."""
		self.frame_pointer = 0
	
	def add_frame_listener(self, frame_index, listener):
		"""Registers a method (``listener``) to be called when a specific 
		frame number (``frame_index``) in the animation has been reached.
		Negative numbers, like Python list indexes, indicate a number of
		frames from the last frame.  That is, a ``frame_index`` of -1 will
		trigger on the last frame of the animation.
		"""
		self.frame_listeners.append((frame_index, listener))
	
	def notify_frame_listeners(self):
		for frame_listener in self.frame_listeners:
			(index, listener) = frame_listener
			if index >= 0 and self.frame_pointer == index:
				listener()
			elif self.frame_pointer == (len(self.frames) + index):
				listener()
	
	def next_frame(self):
		"""Returns the frame to be shown, or None if there is no frame."""
		if self.frame_pointer >= len(self.frames):
			return None
		
		# Important: Notify the frame listeners before frame_pointer has been advanced.
		# Only notify the listeners if this is the first time this frame has been shown
		# (such as if frame_time is > 1).
		if self.frame_time_counter == self.frame_time:
			self.notify_frame_listeners()
		
		frame = self.frames[self.frame_pointer]
		self.frame_time_counter -= 1
		
		if len(self.frames) > 1 and self.frame_time_counter == 0:
			if (self.frame_pointer == len(self.frames)-1):
				if self.repeat:
					self.frame_pointer = 0
				elif not self.hold:
					self.frame_pointer += 1
			else:
				self.frame_pointer += 1

		if self.frame_time_counter == 0:
			self.frame_time_counter = self.frame_time
		
		return frame


class FrameQueueLayer(Layer):
	"""Queue of frames displayed sequentially, as an animation.  Optionally holds the last frame on-screen.
	Destroys the frame list as it displays frames.  In that respect this class implements the old behavior
	of :class:`AnimatedLayer`.
	"""
	def __init__(self, opaque=False, hold=True, repeat=False, frame_time=1, frames=None):
		super(FrameQueueLayer, self).__init__(opaque)
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
	
	fill_color = None
	"""Dot value to fill the frame with.  Requres that ``width`` and ``height`` be set.  If ``None`` only the font characters will be drawn."""
	
	def __init__(self, x, y, font, justify="left", opaque=False, width=128, height=32, fill_color=None):
		super(TextLayer, self).__init__(opaque)
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.fill_color = fill_color
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
			x, y = 0, 0
			if self.justify == 'left':
				(x, y) = (0,0)
			elif self.justify == 'right':
				(x, y) = (-w,0)
			elif self.justify == 'center':
				(x, y) = (-w/2,0)

			if self.fill_color != None:
				self.set_target_position(0, 0)
				self.frame = Frame(width=self.width, height=self.height)
				self.frame.fill_rect(0, 0, self.width, self.height, self.fill_color)
				self.font.draw(self.frame, text, self.x + x, self.y + y)
			else:
				self.set_target_position(self.x, self.y)
				(w, h) = self.font.size(text)
				self.frame = Frame(w, h)
				self.font.draw(self.frame, text, 0, 0)
				(self.target_x_offset, self.target_y_offset) = (x,y)

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
		self.is_new_script_item = True
		self.last_layer = None
	
	def next_frame(self):
		# This assumes looping.  TODO: Add code to not loop!
		if self.frame_start_time == None:
			self.frame_start_time = time.time()
		
		script_item = self.script[self.script_index]
		
		time_on_frame = time.time() - self.frame_start_time
		
		# If we are being forced to the next frame, or if the current script item has expired:
		if self.force_direction != None or time_on_frame > script_item['seconds']:
			
			self.last_layer = script_item['layer']
			
			# Update the script index:
			if self.force_direction == False:
				if self.script_index == 0:
					self.script_index = len(self.script)-1 
				else:
					self.script_index -= 1
			else:
				if self.script_index == len(self.script):
					self.script_index = 0
				else:
					self.script_index += 1
			
			# Only force one item.
			self.force_direction = None
			
			# If we are at the end of the script, reset to the beginning:
			if self.script_index == len(self.script):
				self.script_index = 0
				if self.on_complete != None:
					self.on_complete()
			
			# Assign the new script item:
			script_item = self.script[self.script_index]
			self.frame_start_time = time.time()
			layer = script_item['layer']
			if layer:
				layer.reset()
			self.is_new_script_item = True
		
		# Composite the current script item's layer:
		layer = script_item['layer']
		
		transition = None
		if layer and layer.transition:
			if self.is_new_script_item:
				layer.transition.start()
		
		self.is_new_script_item = False
		
		if layer:
			self.buffer.clear()
			
			# If the layer is opaque we can composite the last layer onto our buffer
			# first.  This will allow us to do transitions between script 'frames'.
			if self.last_layer and self.opaque:
				self.last_layer.composite_next(self.buffer)
			
			layer.composite_next(self.buffer)
			return self.buffer
		else:
			# If this script item has None set for its layer, return None (transparent):
			return None

	def force_next(self, forward=True):
		"""Advances to the next script element in the given direction."""
		self.force_direction = forward
	
	def duration(self):
		"""Returns the complete duration of the script."""
		seconds = 0
		for script_item in self.script:
			seconds += script_item['seconds']
		return seconds


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

	def reset(self):
		for layer in self.layers:
			layer.reset()

	def next_frame(self):		
		layers = []
		for layer in self.layers[::-1]:
			layers.append(layer)
			if layer.opaque:
				break # if we have an opaque layer we don't render any lower layers
				
		self.buffer.clear()
		composited_count = 0
		for layer in layers[::-1]:
			frame = None
			if layer.enabled:
				frame = layer.composite_next(self.buffer)
			if frame != None:
				composited_count += 1
		if composited_count == 0:
			return None
		return self.buffer

class PanningLayer(Layer):
	"""Pans a frame about on a 128x32 buffer, bouncing when it reaches the boundaries."""
	def __init__(self, width, height, frame, origin, translate, bounce=True):
		super(PanningLayer, self).__init__()
		self.buffer = Frame(width, height)
		self.frame = frame
		self.origin = origin
		self.original_origin = origin
		self.translate = translate
		self.bounce = bounce
		self.tick = 0
		# Make sure the translate value doesn't cause us to do any strange movements:
		if width == frame.width:
			self.translate = (0, self.translate[1])
		if height == frame.height:
			self.translate = (self.translate[0], 0)

	def reset(self):
		self.origin = self.original_origin
	
	def next_frame(self):
		self.tick += 1
		if (self.tick % 6) != 0:
			return self.buffer
		Frame.copy_rect(dst=self.buffer, dst_x=0, dst_y=0, src=self.frame, src_x=self.origin[0], src_y=self.origin[1], width=self.buffer.width, height=self.buffer.height)
		if self.bounce and (self.origin[0] + self.buffer.width + self.translate[0] > self.frame.width) or (self.origin[0] + self.translate[0] < 0):
			self.translate = (self.translate[0] * -1, self.translate[1])
		if self.bounce and (self.origin[1] + self.buffer.height + self.translate[1] > self.frame.height) or (self.origin[1] + self.translate[1] < 0):
			self.translate = (self.translate[0], self.translate[1] * -1)
		self.origin = (self.origin[0] + self.translate[0], self.origin[1] + self.translate[1])
		return self.buffer

