from game import *

class BallSave(Mode):
	"""Keeps track of ball save timer."""
	def __init__(self, game, lamp):
		super(BallSave, self).__init__(game, 3)
		self.lamp = lamp
		self.num_balls_to_save = 1
		self.mode_begin = 0
		self.allow_multiple_saves = False
		self.timer = 0

	def mode_started(self):
		pass

	def mode_stopped(self):
		self.lamp.disable()

	def add(self, add_time):
		self.timer += add_time
		if self.timer > 5:
			self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)

	def disable(self):
		self.timer = 0
		self.lamp.disable()

	def start(self, num_balls_to_save=1, time=12, now=True, allow_multiple_saves=False):
		self.allow_multiple_saves = allow_multiple_saves
		self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)
		self.num_balls_to_save = num_balls_to_save
		if now and self.timer <= 0:
			self.timer = time
			print "heyyyyy"
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)
		else:
			print "hoooooo"
			print time
			self.mode_begin = 1
			self.timer_hold = time

	def timer_countdown(self):
		self.timer -= 1
		if (self.timer >= 1):
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)

		if (self.timer == 2):
			self.lamp.disable()
		elif (self.timer == 5):
			self.lamp.schedule(schedule=0x55555555, cycle_seconds=0, now=True)

	# Use this to keep trough4 switch from propogating to other modes
#	def sw_trough4_closed(self, sw):
#		if self.game.machineType == 'sternWhitestar' or self.game.machineType == 'sternSAM':
#                	if self.timer:
#				return True
#
#	def sw_trough4_closed_for_200ms(self, sw):
#		if self.game.machineType == 'sternWhitestar' or self.game.machineType == 'sternSAM':
#               		if self.timer:
#				if self.allow_multiple_saves == 0:
#					self.timer = 2
#					self.lamp.disable()
#				if self.game.switches.trough1.is_closed():
#					self.game.coils.trough.pulse(20)
#				else:
#					self.delay(name='ball_save_eject', event_type=None, delay=1, handler=self.eject)
	# Use this to keep trough1 switch from propogating to other modes
#	def sw_trough1_open(self, sw):
#		if self.game.machineType == 'wpc':
#                	if self.timer:
#				return True

#	def sw_trough1_open_for_200ms(self, sw):
#		if self.game.machineType == 'wpc':
#               		if self.timer:
#				if self.allow_multiple_saves == 0:
#					self.timer = 1
#					self.lamp.disable()
#				if self.game.switches.trough6.is_open():
#					self.game.coils.trough.pulse(20)
#				else:
#					self.delay(name='ball_save_eject', event_type=None, delay=1, handler=self.eject)

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

	def sw_shooterR_open_for_1s(self, sw):
		print "hiiiii"
		print self.timer 
		print self.num_balls_to_save
		if self.mode_begin:
			self.timer = self.timer_hold
			self.mode_begin = 0
			self.lamp.schedule(schedule=0xFF00FF00, cycle_seconds=0, now=True)
			self.delay(name='ball_save_timer', event_type=None, delay=1, handler=self.timer_countdown)

