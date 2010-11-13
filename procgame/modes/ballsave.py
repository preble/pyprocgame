from ..game import Mode

class BallSave(Mode):
	"""Manages a game's ball save functionality by Keeping track of ball save timer and the number of balls to be saved.

	Parameters:

		'game': Parent game object.
		'lamp": Name of lamp to blink while ball save is active.
		'delayed_start_switch': Optional - Name of switch who's inactive event will cause the ball save timer to start (ie. Shooter Lane).
	""" 
	def __init__(self, game, lamp, delayed_start_switch='None'):
		super(BallSave, self).__init__(game, 3)
		self.lamp = lamp
		self.num_balls_to_save = 1
		self.mode_begin = 0
		self.allow_multiple_saves = False
		self.timer = 0
		if delayed_start_switch != 'None' and delayed_start_switch != 'none':
			self.add_switch_handler(name=delayed_start_switch, event_type='inactive', delay=1.0, handler=self.delayed_start_handler)

		""" Optional method to be called when a ball is saved.  Should be defined externally."""
		self.callback = None

		""" Optional method to be called to tell a trough to save balls.  Should be linked externally to an enable method for a trough."""
		self.trough_enable_ball_save = None

	def mode_stopped(self):
		self.disable()

	def launch_callback(self):
		"""Disables the ball save logic when multiple saves are not allowed.  This is typically linked to a Trough object so the trough can notify this logic when a ball is being saved.  If 'self.callback' is externally defined, that method will be called from here."""
		if not self.allow_multiple_saves:
			self.disable()
		if self.callback:
			self.callback()

	def start_lamp(self):
		"""Starts blinking the ball save lamp.  Oftentimes called externally to start blinking the lamp before a ball is plunged."""
		self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)

	def update_lamps(self):
		if self.timer > 5:
			self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)
		elif self.timer > 2:
			self.lamp.schedule(schedule=0x55555555, cycle_seconds=0, now=True)
		else:
			self.lamp.disable()

	def add(self, add_time, allow_multiple_saves=True):
		"""Adds time to the ball save timer."""
		if self.timer >= 1:
			self.timer += add_time
			self.update_lamps()
		else:
			self.start(self.num_balls_to_save, add_time, True, allow_multiple_saves)

	def disable(self):
		"""Disables the ball save logic."""
		if self.trough_enable_ball_save:
			self.trough_enable_ball_save(False)
		self.timer = 0
		self.lamp.disable()
		#self.callback = None

	def start(self, num_balls_to_save=1, time=12, now=True, allow_multiple_saves=False):
		"""Activates the ball save logic."""
		self.allow_multiple_saves = allow_multiple_saves
		self.num_balls_to_save = num_balls_to_save
		if time > self.timer: self.timer = time
		self.update_lamps()
		if now:
			self.cancel_delayed('ball_save_timer')
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)
			if self.trough_enable_ball_save:
				self.trough_enable_ball_save(True)
		else:
			self.mode_begin = 1
			self.timer_hold = time

	def timer_countdown(self):
		self.timer -= 1
		if (self.timer >= 1):
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)
		else:
			self.disable()

		self.update_lamps()

	def is_active(self):
		return self.timer > 0

	def get_num_balls_to_save(self):
		"""Returns the number of balls that can be saved.  Typically this is linked to a Trough object so the trough can decide if a a draining ball should be saved."""
		return self.num_balls_to_save

	def saving_ball(self):
		if not self.allow_multiple_saves:
			self.timer = 1
			self.lamp.disable()

	def delayed_start_handler(self, sw):
		if self.mode_begin:
			self.timer = self.timer_hold
			self.mode_begin = 0
			self.update_lamps()
			self.cancel_delayed('ball_save_timer')
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)
			if self.trough_enable_ball_save:
				self.trough_enable_ball_save(True)

