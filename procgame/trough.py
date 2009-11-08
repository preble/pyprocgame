from game import *

class Trough(Mode):
	"""Manages trough."""
	def __init__(self, game, position_switchnames, eject_switchname, eject_coilname, \
                     early_save_switchnames, shooter_lane_switchname, drain_callback):
		super(Trough, self).__init__(game, 90)
		self.position_switchnames = position_switchnames
		self.eject_switchname = eject_switchname
		self.eject_coilname = eject_coilname
		self.shooter_lane_switchname = shooter_lane_switchname
		self.drain_callback = drain_callback

		# Install switch handlers.
		# Use a delay of 500ms which should ensure balls are settled.
		for switch in position_switchnames:
			self.add_switch_handler(name=switch, event_type='active', delay=.500, handler=self.position_switch_handler)

		# Install early ball_save switch handlers.
		for switch in early_save_switchnames:
			self.add_switch_handler(name=switch, event_type='active', delay=None, handler=self.early_save_switch_handler)
	
		self.num_balls_in_play = 0
		self.num_balls_locked = 0
		self.ball_save_active = False
		self.num_balls_to_launch = 0
		self.num_balls_to_stealth_launch = 0
		self.launch_in_progress = False

	def early_save_switch_handler(self, sw):
		if self.ball_save_active:
			if self.game.switches[self.eject_switchname].is_active():
				self.launch_balls(1, self.ball_save_callback)


	def position_switch_handler(self, sw):
		# Base future calculations on how many balls the machine thinks are currently
		# installed.
                num_current_machine_balls = self.game.num_balls_total
		if self.ball_save_active:
			
			# Calculate how many balls shouldn't be in the trough assuming one just drained
			num_balls_out = self.num_balls_locked + (self.game.ball_save.num_balls_to_save -1)
			# Translate that to how many balls should be in the trough if one is being saved.
			balls_in_trough = num_current_machine_balls - num_balls_out

			if (self.num_balls() - self.num_balls_to_launch) >= balls_in_trough:
				self.launch_balls(1, self.ball_save_callback)
			else:
				# If there are too few balls in the trough.  Ignore this one in an attempt to correct the tracking.
				return 'ignore'
		else:
			num_trough_balls_if_ball_ending = num_current_machine_balls - self.num_balls_locked
			num_trough_balls_if_multiball_ending = num_trough_balls_if_ball_ending - 1
			num_trough_balls_if_multiball_drain = num_trough_balls_if_ball_ending - (self.num_balls_in_play - 1)

			if self.num_balls() == num_trough_balls_if_ball_ending:
				self.num_balls_in_play = 0
				self.drain_callback()
			# Shouldn't need this, but it fixes situations where num_balls_in_play tracking
			# fails, and those situations are still occuring.
			elif self.num_balls() == num_trough_balls_if_multiball_ending:
				self.num_balls_in_play = 1
				self.drain_callback()
			# Check to see if the number of balls in the trough
			# indicate a ball is newly out of play (rather than the
			# trough switches simply being reactivated do to machine
			# shaking or something).
			elif self.num_balls() == num_trough_balls_if_multiball_drain:
				# Fix num_balls_in_play if too low.
				if self.num_balls_in_play < 3:
					self.num_balls_in_play = 2
				# otherwise subtract 1
				else:
					self.num_balls_in_play -= 1
				self.drain_callback()
			

	def is_full(self):
		return self.game.num_balls_total == self.num_balls()

	def num_balls(self):
		ball_count = 0
		for switch in self.position_switchnames:
			if self.game.switches[switch].is_active():
				ball_count += 1
		return ball_count

	def launch_balls(self, num, callback='None', stealth=False):
		self.num_balls_to_launch += num
		if stealth:
			self.num_balls_to_stealth_launch += num
		if not self.launch_in_progress:
			self.launch_in_progress = True
			self.launch_callback = callback
			self.common_launch_code()

	def common_launch_code(self):
		if self.game.switches[self.shooter_lane_switchname].is_inactive():
			self.num_balls_to_launch -= 1
			self.game.coils[self.eject_coilname].pulse(40)
			if self.num_balls_to_stealth_launch > 0:
				self.num_balls_to_stealth_launch -= 1
			else:
				self.num_balls_in_play += 1
			if self.num_balls_to_launch > 0:
                       		self.delay(name='launch', event_type=None, delay=1.0, handler=self.shooter_lane_check)
			else:
				self.launch_in_progress = False
				if self.launch_callback != 'None':
					self.launch_callback()
		else:
			self.delay(name='launch', event_type=None, delay=1.0, handler=self.shooter_lane_check)

	def shooter_lane_check(self):
		if self.game.switches[self.shooter_lane_switchname].is_inactive():
			self.common_launch_code()
		else:
                       	self.delay(name='launch', event_type=None, delay=1.0, handler=self.shooter_lane_check)
