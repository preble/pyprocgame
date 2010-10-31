from ..game import Mode

class Trough(Mode):
	"""Manages trough by providing the following functionality:

		- Keeps track of the number of balls in play
		- Keeps track of the number of balls in the trough
		- Launches one or more balls on request and calls a launch_callback when complete, if one exists.
		- Auto-launches balls while ball save is active (if linked to a ball save object
		- Identifies when balls drain and calls a registered drain_callback, if one exists.
		- Maintains a count of balls locked in playfield lock features (if externally incremented) and adjusts the count of number of balls in play appropriately.  This will help the drain_callback distinguish between a ball ending or simply a multiball ball draining.

	Parameters:

		'game': Parent game object.
		'position_switchnames': List of switchnames for each ball position in the trough.
		'eject_switchname': Name of switch in the ball position the feeds the shooter lane.
		'eject_coilname': Name of coil used to put a ball into the shooter lane.
		'early_save_switchnames': List of switches that will initiate a ball save before the draining ball reaches the trough (ie. Outlanes).
		'shooter_lane_switchname': Name of the switch in the shooter lane.  This is checked before a new ball is ejected.
		'drain_callback': Optional - Name of method to be called when a ball drains (and isn't saved).	
	"""
	def __init__(self, game, position_switchnames, eject_switchname, eject_coilname, \
                     early_save_switchnames, shooter_lane_switchname, drain_callback=None):
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
				delay=None, handler=self.position_switch_handler)

		for switch in position_switchnames:
			self.add_switch_handler(name=switch, event_type='inactive', \
				delay=None, handler=self.position_switch_handler)

		# Install early ball_save switch handlers.
		for switch in early_save_switchnames:
			self.add_switch_handler(name=switch, event_type='active', \
				delay=None, handler=self.early_save_switch_handler)
	
		# Reset variables
		self.num_balls_in_play = 0
		self.num_balls_locked = 0
		self.num_balls_to_launch = 0
		self.num_balls_to_stealth_launch = 0
		self.launch_in_progress = False

		self.ball_save_active = False

		""" Callback called when a ball is saved.  Used optionally only when ball save is enabled (by a call to :meth:`Trough.enable_ball_save`).  Set externally if a callback should be used. """
		self.ball_save_callback = None

		""" Method to get the number of balls to save.  Set externally when using ball save logic."""
		self.num_balls_to_save = None

		self.launch_callback = None

		#self.debug()

	def debug(self):
		self.game.set_status(str(self.num_balls_in_play) + "," + str(self.num_balls_locked))
       		self.delay(name='launch', event_type=None, delay=1.0, \
				           handler=self.debug)

	def enable_ball_save(self, enable=True):
		"""Used to enable/disable ball save logic."""
		self.ball_save_active = enable

	def early_save_switch_handler(self, sw):
		if self.ball_save_active:
			# Only do an early ball save if a ball is ready to be launched.
			# Otherwise, let the trough switches take care of it.
			if self.game.switches[self.eject_switchname].is_active():
				self.launch_balls(1, self.ball_save_callback, \
						  stealth=True)

	def mode_stopped(self):
		self.cancel_delayed('check_switches')

	# Switches will change states a lot as balls roll down the trough.
	# So don't go through all of the logic every time.  Keep resetting a
	# delay function when switches change state.  When they're all settled,
	# the delay will call the real handler (check_switches).
	def position_switch_handler(self, sw):
		self.cancel_delayed('check_switches')
		self.delay(name='check_switches', event_type=None, delay=0.50, handler=self.check_switches)

	def check_switches(self):
		if self.num_balls_in_play > 0:
			# Base future calculations on how many balls the machine 
			# thinks are currently installed.
       	         	num_current_machine_balls = self.game.num_balls_total
			temp_num_balls = self.num_balls()
			if self.ball_save_active:

				if self.num_balls_to_save:
					num_balls_to_save = self.num_balls_to_save()
				else:
					num_balls_to_save = 0
				
				# Calculate how many balls shouldn't be in the 
				# trough assuming one just drained
				num_balls_out = self.num_balls_locked + \
					(num_balls_to_save - 1)
				# Translate that to how many balls should be in 
				# the trough if one is being saved.
				balls_in_trough = num_current_machine_balls - \
						  num_balls_out
	
				if (temp_num_balls - \
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

				if temp_num_balls == num_current_machine_balls or \
				   temp_num_balls == num_trough_balls_if_ball_ending:
					self.num_balls_in_play = 0
					if self.drain_callback:
						self.drain_callback()
				# Multiball is ending if all but 1 ball are in the trough.
				# Shouldn't need this, but it fixes situations where 
				# num_balls_in_play tracking
				# fails, and those situations are still occuring.
				elif temp_num_balls == \
				     num_trough_balls_if_multiball_ending:
					self.num_balls_in_play = 1
					if self.drain_callback:
						self.drain_callback()
				# Otherwise, another ball from multiball is draining 
				# if the trough gets one more than it would have if 
				# all num_balls_in_play are not in the trough.
				elif temp_num_balls ==  \
				     num_trough_balls_if_multiball_drain:
					# Fix num_balls_in_play if too low.
					if self.num_balls_in_play < 3:
						self.num_balls_in_play = 2
					# otherwise subtract 1
					else:
						self.num_balls_in_play -= 1
					if self.drain_callback:
						self.drain_callback()

	# Count the number of balls in the trough by counting active trough switches.
	def num_balls(self):
		"""Returns the number of balls in the trough."""
		ball_count = 0
		for switch in self.position_switchnames:
			if self.game.switches[switch].is_active():
				ball_count += 1
		return ball_count

	def is_full(self):
		return self.num_balls() == self.game.num_balls_total

	# Either initiate a new launch or add another ball to the count of balls
	# being launched.  Make sure to keep a separate count for stealth launches
	# that should not increase num_balls_in_play.
	def launch_balls(self, num, callback=None, stealth=False):
		"""Launches balls into play.

			'num': Number of balls to be launched.  
			If ball launches are still pending from a previous request, 
			this number will be added to the previously requested number.

			'callback': If specified, the callback will be called once
			all of the requested balls have been launched.

			'stealth': Set to true if the balls being launched should NOT
			be added to the number of balls in play.  For instance, if
			a ball is being locked on the playfield, and a new ball is 
			being launched to keep only 1 active ball in play,
			stealth should be used.
		"""

		self.num_balls_to_launch += num
		if stealth:
			self.num_balls_to_stealth_launch += num
		if not self.launch_in_progress:
			self.launch_in_progress = True
			if callback:
				self.launch_callback = callback
			self.common_launch_code()

	# This is the part of the ball launch code that repeats for multiple launches.
	def common_launch_code(self):
		# Only kick out another ball if the last ball is gone from the 
		# shooter lane.	
		if self.game.switches[self.shooter_lane_switchname].is_inactive():
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
				if self.launch_callback:
					self.launch_callback()
		# Otherwise, wait 1 second before trying again.
		else:
			self.delay(name='launch', event_type=None, delay=1.0, \
				   handler=self.common_launch_code)
