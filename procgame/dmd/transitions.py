from dmd import *

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
		frame = from_frame.copy()
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

class SlideOverTransition(LayerTransitionBase):
	def __init__(self, direction='north'):
		super(SlideOverTransition, self).__init__()
		self.direction = direction
		self.progress_per_frame = 1.0/15.0
	def transition_frame(self, from_frame, to_frame):
		frame = from_frame.copy()
		dst_x, dst_y = 0, 0
		prog = self.progress
		if self.in_out == 'in':
			prog = 1.0 - prog
		dst_x, dst_y = {
		 'north': (0,  prog*frame.height),
		 'south': (0, -prog*frame.height),
		 'east':  (-prog*frame.width, 0),
		 'west':  ( prog*frame.width, 0),
		}[self.direction]
		Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
		return frame

class PushTransition(LayerTransitionBase):
	def __init__(self, direction='north'):
		super(PushTransition, self).__init__()
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
		 'north': (0,  prog*frame.height,  0, -prog1*frame.height),
		 'south': (0, -prog*frame.height,  0,  prog1*frame.height),
		 'east':  (-prog*frame.width, 0,    prog1*frame.width, 0),
		 'west':  ( prog*frame.width, 0,   -prog1*frame.width, 0),
		}[self.direction]
		Frame.copy_rect(dst=frame, dst_x=dst_x, dst_y=dst_y, src=to_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
		Frame.copy_rect(dst=frame, dst_x=dst_x1, dst_y=dst_y1, src=from_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
		return frame

class WipeTransition(LayerTransitionBase):
	def __init__(self, direction='north'):
		super(WipeTransition, self).__init__()
		self.direction = direction
		self.progress_per_frame = 1.0/15.0
	def transition_frame(self, from_frame, to_frame):
		frame = Frame(width=from_frame.width, height=from_frame.height)
		prog0 = self.progress
		prog1 = self.progress
		if self.in_out == 'out':
			prog0 = 1.0 - prog0
		else:
			prog1 = 1.0 - prog1
		src_x, src_y = {
		 'north': (0,  prog1*frame.height),
		 'south': (0,  prog0*frame.height),
		 'east':  (prog0*frame.width, 0),
		 'west':  (prog1*frame.width, 0),
		}[self.direction]
		if self.direction in ['east', 'south']:
			from_frame, to_frame = to_frame, from_frame
		src_x = int(round(src_x))
		src_y = int(round(src_y))
		Frame.copy_rect(dst=frame, dst_x=0, dst_y=0, src=from_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
		Frame.copy_rect(dst=frame, dst_x=src_x, dst_y=src_y, src=to_frame, src_x=src_x, src_y=src_y, width=from_frame.width-src_x, height=from_frame.height-src_y, op='copy')
		return frame


class ObscuredWipeTransition(LayerTransitionBase):
	def __init__(self, obscuring_frame, composite_op, direction='north'):
		super(ObscuredWipeTransition, self).__init__()
		self.composite_op = composite_op
		self.direction = direction
		self.progress_per_frame = 1.0/15.0
		self.obs_frame = obscuring_frame
	
	def transition_frame(self, from_frame, to_frame):
		frame = Frame(width=from_frame.width, height=from_frame.height)
		prog0 = self.progress
		prog1 = self.progress
		if self.in_out == 'out':
			prog0 = 1.0 - prog0
		else:
			prog1 = 1.0 - prog1
		# TODO: Improve the src_x/y so that it moves at the same speed as ovr_x/y, with the midpoint.
		src_x, src_y, ovr_x, ovr_y = {
		 'north': (0,  prog1*frame.height,   0,  frame.height-prog0*(self.obs_frame.height+2*frame.height)),
		 'south': (0,  prog0*frame.height,   0,  frame.height-prog1*(self.obs_frame.height+2*frame.height)),
		 'east':  (prog0*frame.width, 0,     frame.width-prog1*(self.obs_frame.width+2*frame.width), 0),
		 'west':  (prog1*frame.width, 0,     frame.width-prog0*(self.obs_frame.width+2*frame.width), 0),
		}[self.direction]
		if self.direction in ['east', 'south']:
			from_frame, to_frame = to_frame, from_frame
		src_x = int(round(src_x))
		src_y = int(round(src_y))
		Frame.copy_rect(dst=frame, dst_x=0, dst_y=0, src=from_frame, src_x=0, src_y=0, width=from_frame.width, height=from_frame.height, op='copy')
		Frame.copy_rect(dst=frame, dst_x=src_x, dst_y=src_y, src=to_frame, src_x=src_x, src_y=src_y, width=from_frame.width-src_x, height=from_frame.height-src_y, op='copy')
		Frame.copy_rect(dst=frame, dst_x=ovr_x, dst_y=ovr_y, src=self.obs_frame, src_x=0, src_y=0, width=self.obs_frame.width, height=self.obs_frame.height, op=self.composite_op)
		return frame


class CrossFadeTransition(LayerTransitionBase):
	"""Performs a cross-fade between two layers.  As one fades out the other one fades in."""
	def __init__(self, width=128, height=32):
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
