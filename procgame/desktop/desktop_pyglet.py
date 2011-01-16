import procgame.config
import procgame.dmd
import pinproc
import pyglet
import pyglet.image
import pyglet.window
from pyglet import gl

# Bitmap data for luminance-alpha mask image.
# See image_to_string below for code to generate this:
MASK_DATA = """\x00\xec\x00\xc8\x00\x7f\x00\x5a\x00\x5a\x00\x7f\x00\xc8\x00\xed\x00\xc8\x00\x5a\x00\x36\x00\x11\x00\x11\x00\x36\x00\x5a\x00\xc8\x00\x7f\x00\x36\xff\x00\xff\x00\xff\x00\xff\x00\x00\x36\x00\x7e\x00\x5a\x00\x10\xff\x00\xff\x00\xff\x00\xff\x00\x00\x11\x00\x5a\x00\x5a\x00\x11\xff\x00\xff\x00\xff\x00\xff\x00\x00\x11\x00\x5a\x00\x7e\x00\x36\xff\x00\xff\x00\xff\x00\xff\x00\x00\x35\x00\x7f\x00\xc8\x00\x5a\x00\x36\x00\x11\x00\x11\x00\x35\x00\x5a\x00\xc8\x00\xed\x00\xc8\x00\x7e\x00\x5a\x00\x5a\x00\x7f\x00\xc8\x00\xed"""
MASK_SIZE = 8

DMD_SIZE = (128, 32)
DMD_SCALE = int(procgame.config.value_for_key_path('desktop_dmd_scale', str(MASK_SIZE)))

class Desktop(object):
	"""The :class:`Desktop` class helps manage interaction with the desktop, providing both a windowed
	representation of the DMD, as well as translating keyboard input into pyprocgame events."""
	
	exit_event_type = 99
	"""Event type sent when Ctrl-C is received."""
	
	key_map = {}
	
	window = None
	
	def __init__(self):
		self.key_events = []
		self.setup_window()
		self.add_key_map(pyglet.window.key.LSHIFT, 3)
		self.add_key_map(pyglet.window.key.RSHIFT, 1)
		self.frame_drawer = FrameDrawer()
	
	def add_key_map(self, key, switch_number):
		"""Maps the given *key* to *switch_number*, where *key* is one of the key constants in :mod:`pygame.locals`."""
		self.key_map[key] = switch_number

	def clear_key_map(self):
		"""Empties the key map."""
		self.key_map = {}

	def get_keyboard_events(self):
		"""Asks :mod:`pygame` for recent keyboard events and translates them into an array
		of events similar to what would be returned by :meth:`pinproc.PinPROC.get_events`."""
		if self.window.has_exit:
			self.append_exit_event()
		e = self.key_events
		self.key_events = []
		return e
	
	def append_exit_event(self):
		self.key_events.append({'type':self.exit_event_type, 'value':'quit'})

	def setup_window(self):
		self.window = pyglet.window.Window(width=DMD_SIZE[0]*DMD_SCALE, height=DMD_SIZE[1]*DMD_SCALE)
		
		@self.window.event
		def on_close():
			self.append_exit_event()
		
		@self.window.event
		def on_key_press(symbol, modifiers):
			if (symbol == pyglet.window.key.C and modifiers & pyglet.window.key.MOD_CTRL) or (symbol == pyglet.window.key.ESCAPE):
				self.append_exit_event()
			elif symbol in self.key_map:
				self.key_events.append({'type':pinproc.EventTypeSwitchClosedDebounced, 'value':self.key_map[symbol]})
		
		@self.window.event
		def on_key_release(symbol, modifiers):
			if symbol in self.key_map:
				self.key_events.append({'type':pinproc.EventTypeSwitchOpenDebounced, 'value':self.key_map[symbol]})

	def draw(self, frame):
		"""Draw the given :class:`~procgame.dmd.Frame` in the window."""
		self.window.dispatch_events()
		self.window.clear()
		self.frame_drawer.draw(frame)
		self.window.flip()

	def __str__(self):
		return '<Desktop pyglet>'


class FrameDrawer(object):
	"""Manages drawing a DMD frame using pyglet."""
	def __init__(self):
		super(FrameDrawer, self).__init__()
		self.mask = pyglet.image.ImageData(MASK_SIZE, MASK_SIZE, 'LA', MASK_DATA, pitch=16)
		self.mask_texture = pyglet.image.TileableTexture.create_for_image(self.mask)
	
	def draw(self, frame):
		# The gneneral plan here is:
		#  1. Get the dots in the range of 0-255.
		#  2. Create a texture with the dots data.
		#  3. Draw the texture, scaled up with nearest-neighbor.
		#  4. Draw a mask over the dots to give them a slightly more realistic look.
		
		gl.glEnable(gl.GL_BLEND)
		gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
		gl.glLoadIdentity()
		
		# Draw the dots in this color:
		gl.glColor3f(1.0, 0.5, 0.25)

		gl.glScalef(1, -1, 1)
		gl.glTranslatef(0, -DMD_SIZE[1]*DMD_SCALE, 0)

		data = frame.get_data_mult()
		image = pyglet.image.ImageData(DMD_SIZE[0], DMD_SIZE[1], 'L', data, pitch=DMD_SIZE[0])

		gl.glTexParameteri(image.get_texture().target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
		image.blit(0, 0, width=DMD_SIZE[0]*DMD_SCALE, height=DMD_SIZE[1]*DMD_SCALE)

		del image

		gl.glScalef(DMD_SCALE/float(MASK_SIZE), DMD_SCALE/float(MASK_SIZE), 1.0)
		gl.glColor4f(1.0, 1.0, 1.0, 1.0)
		self.mask_texture.blit_tiled(x=0, y=0, z=0, width=DMD_SIZE[0]*MASK_SIZE, height=DMD_SIZE[1]*MASK_SIZE)


def image_to_string(filename):
	"""Generate a string representation of the image at the given path, for embedding in code."""
	image = pyglet.image.load(filename)
	data = image.get_data('LA', 16)
	s = ''
	for x in data:
		s += "\\x%02x" % (ord(x))
	return s
