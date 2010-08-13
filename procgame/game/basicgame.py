from . import GameController
from ..dmd import DisplayController, font_named
from ..modes import ScoreDisplay
from ..desktop import Desktop
from .. import config
import pinproc

class BasicGame(GameController):
	""":class:`BasicGame` is a subclass of :class:`~procgame.game.GameController` 
	that includes and configures various useful helper classes to provide:
	
	* A :class:`~procgame.modes.ScoreDisplay` mode/layer at priority 1, available
	  at ``self.score_display``.
	* A :class:`~procgame.dmd.DisplayController` mode to manage the DMD layers,
	  at ``self.dmd``.
	* A :class:`~procgame.desktop.Desktop` helper at ``self.desktop`` configured 
	  to display the most recent DMD frames on the desktop, as well as interpret
	  keyboard input as switch events.
	
	It is a recommended base class to build your game upon, or use as a template
	if your game has special requirements.
	"""
	
	dmd = None
	score_display = None
	desktop = None
	
	def __init__(self, machine_type):
		super(BasicGame, self).__init__(machine_type)
		self.dmd = DisplayController(self, width=128, height=32, message_font=font_named('Font07x5.dmd'))
		self.score_display = ScoreDisplay(self, 0)
		self.desktop = Desktop()
		self.dmd.frame_handlers.append(self.set_last_frame)
		key_map_config = config.value_for_key_path(keypath='keyboard_switch_map', default={})
		for k, v in key_map_config.items():
			print k, v, pinproc.decode(machine_type, v), machine_type
			self.desktop.add_key_map(ord(str(k)), pinproc.decode(machine_type, v))
	
	def reset(self):
		"""Calls super's reset and adds the :class:`ScoreDisplay` mode to the mode queue."""
		super(BasicGame, self).reset()
		self.modes.add(self.score_display)
		
	def dmd_event(self):
		"""Updates the DMD via :class:`DisplayController`."""
		self.dmd.update()
	
	def get_events(self):
		"""Overriding GameController's implementation in order to append keyboard events."""
		events = super(BasicGame, self).get_events()
		events.extend(self.desktop.get_keyboard_events())
		return events
	
	def tick(self):
		"""Called once per run loop.
		
		Displays the last-received DMD frame on the desktop."""
		self.show_last_frame()

	def score(self, points):
		"""Convenience method to add *points* to the current player."""
		p = self.current_player()
		p.score += points

	#
	# Support for showing the last DMD frame on the desktop.
	#
	#   Because showing each frame on the desktop can be pretty time-consuming,
	#   we show it only once per run loop cycle (via tick()), and only when there
	#   is a new frame (via last_frame).  By showing it this way (and not directly
	#   from DisplayController's frame_handlers), we allow the run loop to progress
	#   quickly without getting bogged down drawing the DMD on the desktop if a 
	#   large number of DMD events arrive 'at once'.
	#
	
	last_frame = None
	
	def set_last_frame(self, frame):
		self.last_frame = frame
	
	def show_last_frame(self):
		if self.last_frame:
			self.desktop.draw(self.last_frame)
			self.last_frame = None

