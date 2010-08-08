import sys
import procgame
import pinproc
from threading import Thread
import random
import string
import time
import locale
import math
import copy
import dmd
import ctypes

try:
	import pygame
	from pygame.locals import *
except ImportError:
	print "Error importing pygame; ignoring."

if hasattr(ctypes.pythonapi, 'Py_InitModule4'):
   Py_ssize_t = ctypes.c_int
elif hasattr(ctypes.pythonapi, 'Py_InitModule4_64'):
   Py_ssize_t = ctypes.c_int64
else:
   raise TypeError("Cannot determine type of Py_ssize_t")

PyObject_AsWriteBuffer = ctypes.pythonapi.PyObject_AsWriteBuffer
PyObject_AsWriteBuffer.restype = ctypes.c_int
PyObject_AsWriteBuffer.argtypes = [ctypes.py_object,
                                  ctypes.POINTER(ctypes.c_void_p),
                                  ctypes.POINTER(Py_ssize_t)]

def array(surface):
   buffer_interface = surface.get_buffer()
   address = ctypes.c_void_p()
   size = Py_ssize_t()
   PyObject_AsWriteBuffer(buffer_interface,
                          ctypes.byref(address), ctypes.byref(size))
   bytes = (ctypes.c_byte * size.value).from_address(address.value)
   bytes.object = buffer_interface
   return bytes


class Desktop():
	"""The :class:`Desktop` class helps manage interaction with the desktop, providing both a windowed
	representation of the DMD, as well as translating keyboard input into pyprocgame events."""
	
	exit_event_type = 99
	"""Event type sent when Ctrl-C is received."""
	
	key_map = {}
	
	def __init__(self):
		self.ctrl = 0
		self.i = 0
		if 'pygame' in globals():
			self.setup_window()
		else:
			print 'Desktop init skipping setup_window(); pygame does not appear to be loaded.'
		self.add_key_map(K_LSHIFT, 3)
		self.add_key_map(K_RSHIFT, 1)
	
	def add_key_map(self, key, value):
		"""Maps the given *key* to *value*, where *key* is one of the key constants in :mod:`pygame.locals`."""
		self.key_map[key] = value
	
	def clear_key_map(self):
		"""Empties the key map."""
		self.key_map = {}

	def get_keyboard_events(self):
		"""Asks :mod:`pygame` for recent keyboard events and translates them into an array
		of events similar to what would be returned by :meth:`pinproc.PinPROC.get_events`."""
		key_events = []
		for event in pygame.event.get():
			key_event = {}
			if event.type == KEYDOWN:
				if event.key == K_RCTRL or event.key == K_LCTRL:
					self.ctrl = 1
				if event.key == K_c:
					if self.ctrl == 1:
						key_event['type'] = self.exit_event_type
						key_event['value'] = 'quit'
				elif (event.key == K_ESCAPE):
					key_event['type'] = self.exit_event_type
					key_event['value'] = 'quit'
				elif event.key in self.key_map:
					key_event['type'] = pinproc.EventTypeSwitchClosedDebounced
					key_event['value'] = self.key_map[event.key]
			elif event.type == KEYUP:
				if event.key == K_RCTRL or event.key == K_LCTRL:
					self.ctrl = 0
				elif event.key in self.key_map:
					key_event['type'] = pinproc.EventTypeSwitchOpenDebounced
					key_event['value'] = self.key_map[event.key]
			if len(key_event):
				key_events.append(key_event)
		return key_events
		
	
	screen = None
	""":class:`pygame.Surface` object representing the screen's surface."""
	screen_multiplier = 2

	def setup_window(self):
		pygame.init()
		self.screen = pygame.display.set_mode((128*self.screen_multiplier, 32*self.screen_multiplier))
		pygame.display.set_caption('Press CTRL-C to exit')

	def draw(self, frame):
		"""Draw the given :class:`~procgame.dmd.Frame` in the window."""
		# Use adjustment to add a one pixel border around each dot, if
		# the screen size is large enough to accomodate it.
		if self.screen_multiplier >= 4:
			adjustment = -1
		else:
			adjustment = 0

		bytes_per_pixel = 4
		y_offset = 128*bytes_per_pixel*self.screen_multiplier*self.screen_multiplier
		x_offset = bytes_per_pixel*self.screen_multiplier

		surface_array = array(self.screen)
		
		frame_string = frame.get_data()
		
		x = 0
		y = 0
		for dot in frame_string:
			color_val = ord(dot)*16
			index = y*y_offset + x*x_offset
			surface_array[index:index+bytes_per_pixel] = (color_val,color_val,color_val,0)
			x += 1
			if x == 128:
				x = 0
				y += 1
		del surface_array

		pygame.display.update()
