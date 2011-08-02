from dmd import *
from layers import *


class DisplayController(object):
	"""Manages the process of obtaining DMD frames from active modes and compositing them together for
	display on the DMD.
	
	**Using DisplayController**
	
	1. Add a :class:`DisplayController` instance to your :class:`~procgame.game.GameController` subclass::
	
	    class Game(game.GameController):
	      def __init__(self, machine_type):
	        super(Game, self).__init__(machine_type)
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
		to apply that layer's next frame to the frame in progress.
		
		The resulting frame is sent to the :attr:`frame_handlers` and then returned from this method."""
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
				
		return frame
