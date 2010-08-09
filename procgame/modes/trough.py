from ..game import Mode

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
		# Use a delay of 750ms which should ensure balls are settled.
		for switch in position_switchnames:
			self.add_switch_handler(name=switch, event_type='active', \
				delay=.750, handler=self.position_switch_handler)

		# Install early ball_save switch handlers.
		for switch in early_save_switchnames:
			self.add_switch_handler(name=switch, event_type='active', \
				delay=None, handler=self.early_save_switch_handler)
	
		# Reset variables
		self.num_balls_in_play = 0
		self.num_balls_locked = 0
		self.ball_save_active = False
		self.num_balls_to_launch = 0
		self.num_balls_to_stealth_launch = 0
		self.launch_in_progress = False

		self.update_is_full()

	def early_save_switch_handler(self, sw):
		if self.ball_save_active:
			# Only do an early ball save if a ball is ready to be launched.
			# Otherwise, let the trough switches take care of it.
			if self.game.switches[self.eject_switchname].is_active():
				self.launch_balls(1, self.ball_save_callback, \
						  stealth=True)


	def position_switch_handler(self, sw):
		self.update_is_full()
		if self.num_balls_in_play > 0:
			# Base future calculations on how many balls the machine 
			# thinks are currently installed.
       	         	num_current_machine_balls = self.game.num_balls_total
			if self.ball_save_active:
				
				# Calculate how many balls shouldn't be in the 
				# trough assuming one just drained
				num_balls_out = self.num_balls_locked + \
					(self.game.ball_save.num_balls_to_save -1)
				# Translate that to how many balls should be in 
				# the trough if one is being saved.
				balls_in_trough = num_current_machine_balls - \
						  num_balls_out
	
				if (self.num_balls() - \
				    self.num_balls_to_launch) >= balls_in_trough:
					self.launch_balls(1, self.ball_save_callback, \
							  stealth=True)
				else:
					# If there are too few balls in the trough.  
					# Ignore this one in an attempt to correct 
					# the tracking.
					return 'ignore'
			else:
				# Calculate how many balls should be in the trough 
				# for various conditions.
				num_trough_balls_if_ball_ending = \
					num_current_machine_balls - self.num_balls_locked
				num_trough_balls_if_multiball_ending = \
					num_trough_balls_if_ball_ending - 1
				num_trough_balls_if_multiball_drain = \
					num_trough_balls_if_ball_ending - \
					(self.num_balls_in_play - 1)
	
	
				# The ball should end if all of the balls 
				# are in the trough.
				if self.is_full or self.num_balls() == \
				                   num_trough_balls_if_ball_ending:
					self.num_balls_in_play = 0
					self.drain_callback()
				# Multiball is ending if all but 1 ball are in the trough.
				# Shouldn't need this, but it fixes situations where 
				# num_balls_in_play tracking
				# fails, and those situations are still occuring.
				elif self.num_balls() == \
				     num_trough_balls_if_multiball_ending:
					self.num_balls_in_play = 1
					self.drain_callback()
				# Otherwise, another ball from multiball is draining 
				# if the trough gets one more than it would have if 
				# all num_balls_in_play are not in the trough.
				elif self.num_balls() ==  \
				     num_trough_balls_if_multiball_drain:
					# Fix num_balls_in_play if too low.
					if self.num_balls_in_play < 3:
						self.num_balls_in_play = 2
					# otherwise subtract 1
					else:
						self.num_balls_in_play -= 1
					self.drain_callback()
				

	def update_is_full(self):
		self.is_full = self.game.num_balls_total == self.num_balls()

	# Count the number of balls in the trough by counting active trough switches.
	def num_balls(self):
		ball_count = 0
		for switch in self.position_switchnames:
			if self.game.switches[switch].is_active():
				ball_count += 1
		return ball_count

	# Either initiate a new launch or add another ball to the count of balls
	# being launched.  Make sure to keep a separate count for stealth launches
	# that should not increase num_balls_in_play.
	def launch_balls(self, num, callback='None', stealth=False):
		self.num_balls_to_launch += num
		if stealth:
			self.num_balls_to_stealth_launch += num
		if not self.launch_in_progress:
			self.launch_in_progress = True
			self.launch_callback = callback
			self.common_launch_code()

	# This is the part of the ball launch code that repeats for multiple launches.
	def common_launch_code(self):
		# Only kick out another ball if the last ball is gone from the 
		# shooter lane.	
		if self.game.switches[self.shooter_lane_switchname].is_inactive():
			self.is_full = False
			self.num_balls_to_launch -= 1
			self.game.coils[self.eject_coilname].pulse(40)
			# Only increment num_balls_in_play if there are no more 
			# stealth launches to complete.
			if self.num_balls_to_stealth_launch > 0:
				self.num_balls_to_stealth_launch -= 1
			else:
				self.num_balls_in_play += 1
			# If more balls need to be launched, delay 1 second 
			if self.num_balls_to_launch > 0:
                       		self.delay(name='launch', event_type=None, delay=1.0, \
				           handler=self.common_launch_code)
			else:
				self.launch_in_progress = False
				if self.launch_callback != 'None':
					self.launch_callback()
		# Otherwise, wait 1 second before trying again.
		else:
			self.delay(name='launch', event_type=None, delay=1.0, \
				   handler=self.common_launch_code)
