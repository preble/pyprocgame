from game import *

class BallSave(Mode):
	"""Keeps track of ball save timer.  Works in conjection with a trough object."""
	def __init__(self, game, lamp, delayed_start_switch='None'):
		super(BallSave, self).__init__(game, 3)
		self.lamp = lamp
		self.num_balls_to_save = 1
		self.mode_begin = 0
		self.allow_multiple_saves = False
		self.timer = 0
		if delayed_start_switch != 'None' and delayed_start_switch != 'none':
			self.add_switch_handler(name=delayed_start_switch, event_type='inactive', delay=1.0, handler=self.delayed_start_handler)

	def mode_started(self):
		self.game.trough.ball_save_callback = self.launch_callback
		
	def mode_stopped(self):
		self.disable()

	def launch_callback(self):
		if not self.allow_multiple_saves:
			self.disable()
		self.game.set_status('Ball Saved!')

	def start_lamp(self):
		self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)

	def update_lamps(self):
		if self.timer > 5:
			self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)
		elif self.timer > 2:
			self.lamp.schedule(schedule=0x55555555, cycle_seconds=0, now=True)
		else:
			self.lamp.disable()

	def add(self, add_time, allow_multiple_saves=True):
		if self.timer >= 1:
			self.timer += add_time
			self.update_lamps()
		else:
			self.start(self.num_balls_to_save, add_time, True, allow_multiple_saves)

	def disable(self):
		self.game.trough.ball_save_active = False
		self.timer = 0
		self.lamp.disable()

	def start(self, num_balls_to_save=1, time=12, now=True, allow_multiple_saves=False):
		self.game.trough.ball_save_active = True
		self.allow_multiple_saves = allow_multiple_saves
		self.num_balls_to_save = num_balls_to_save
		self.timer = time
		self.update_lamps()
		if now and self.timer <= 0:
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)
		else:
			self.mode_begin = 1
			self.timer_hold = time

	def timer_countdown(self):
		self.timer -= 1

		if self.timer < 1:
			self.game.trough.ball_save_active = False

		if (self.timer >= 1):
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)

		self.update_lamps()

	def is_active(self):
		return self.timer > 0

	def saving_ball(self):
		if not self.allow_multiple_saves:
			self.timer = 1
			self.lamp.disable()


	def eject(self):
		if self.game.machineType == 'wpc':
			if self.game.switches.trough6.is_open():
				self.game.coils.trough.pulse(20)
			else:
				self.delay(name='ball_save_eject', event_type=None, delay=1, handler=self.eject)
		elif self.game.machineType == 'sternWhitestar' or self.game.machineType == 'sternSAM':
			if self.game.switches.trough1.is_open():
				self.game.coils.trough.pulse(20)
			else:
				self.delay(name='ball_save_eject', event_type=None, delay=1, handler=self.eject)

	def delayed_start_handler(self, sw):
		if self.mode_begin:
			self.timer = self.timer_hold
			self.mode_begin = 0
			self.update_lamps()
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)

