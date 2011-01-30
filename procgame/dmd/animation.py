import os
import struct
from procgame.dmd import Frame

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
		self.frames = []

	def load(self, filename):
		"""Loads a series of frames from a .dmd (DMDAnimator) file.
		
		File format is as follows: ::
		
		  4 bytes - header data (unused)
		  4 bytes - frame_count
		  4 bytes - width of animation frames in pixels
		  4 bytes - height of animation frames in pixels
		  ? bytes - Frames: frame_count * width * height bytes
		
		Frame data is laid out row0..rowN.  Byte values of each pixel
		are in two parts: the lower 4 bits are the dot "color", ``0x0`` 
		being black and ``0xF`` being the brightest value and the upper 
		4 bits are alpha (``0x0`` is fully transparent, ``0xF`` is fully
		opaque).  Note that transparency is optional and only supported 
		by the alpha blending modes in :meth:`procgame.dmd.Frame.copy_rect`.  
		Alpha values are ignored by :meth:`pinproc.PinPROC.dmd_draw`.
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
