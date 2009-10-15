from procgame import *

class Multiball(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, deadworld_mod_installed):
		super(Multiball, self).__init__(game, priority)
		self.deadworld_mod_installed = deadworld_mod_installed
		self.lock_enabled = 0
		self.num_balls_locked = 0
		self.num_balls_to_eject = 0
		self.num_left_ramp_shots = 0
		self.virtual_locks_needed = 0
		self.banner_layer = dmd.TextLayer(128/2, 7, font_jazz18, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
		self.state = 'load'
		self.displaying_text = 0
		self.enable_ball_save_after_launch=False
	
	def mode_started(self):
		self.game.coils.globeMotor.disable()
		self.lock_lamps()
		self.game.deadworld.initialize()
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 250, True, False)

	def mode_stopped(self):
		self.game.coils.flasherGlobe.disable()
		self.game.lamps.gi04.disable()
		#if self.displaying_text:
		#	self.game.dmd.layers.remove(self.layer)
		#	self.cancel_delayed(['remove_dmd_layer'])

	def is_active(self):
		return self.state == 'multiball'

	def end_multiball(self):
		self.state = 'multiball_complete'
		self.game.set_status(self.state)
		self.game.lamps.gi04.disable()

	def display_text(self, text):
		# use a varable to protect against adding the layer twice
		#if self.displaying_text:
		#	self.game.dmd.layers.remove(self.layer)
		#	self.cancel_delayed(['remove_dmd_layer'])
		#self.displaying_text = 1
		self.banner_layer.set_text(text,3)
		self.game.dmd.layers.append(self.layer)
		self.delay(name='remove_dmd_layer', event_type=None, delay=2.5, handler=self.remove_dmd_layer)

	def remove_dmd_layer(self):
		self.game.dmd.layers.remove(self.layer)
		self.displaying_text = 0

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.state = info_record[0]
			self.num_balls_locked = info_record[1]

		# Virtual locks are needed when there are more balls physically locked 
		# than the player has locked through play.  This happens when
		# another player locks more balls than the current player.  Use
		# Virtual locks > 0 for this case.
		# Use Virtual locks < 0 when the player has locked more balls than are
		# physically locked.  This could happen when another player plays
		# multiball and empties the locked balls.
		if self.deadworld_mod_installed:
			self.virtual_locks_needed = self.game.deadworld.num_balls_locked - self.num_balls_locked

		if self.virtual_locks_needed < 0:
			# enable the lock the player can quickly re-lock
			self.enable_lock()
			self.num_balls_locked = self.game.deadworld.num_balls_locked
			# pre-set the ramp shots to get the lock light blinking appropriately
			self.num_left_ramp_shots = 3
		self.lock_lamps()

	def get_info_record(self):
		info_record = [self.state, self.num_balls_locked]
		return info_record

	def disable_lock(self):
		self.game.deadworld.disable_lock()
		self.lock_enabled = 0
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 250, True, False)

	def enable_lock(self):
		self.display_text("Lock is Lit!")
		self.game.deadworld.enable_lock()
		self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)
		self.lock_enabled = 1
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 250, True, True)
		

	def sw_leftRampToLock_active(self, sw):
		if self.lock_enabled:
			self.game.coils.flasherGlobe.schedule(schedule=0xAAAAAAAA, cycle_seconds=2, now=True)
			self.num_balls_locked += 1
			self.display_text("Ball " + str(self.num_balls_locked) + " Locked!")
			# Player needs to re-fill the locks
			if self.virtual_locks_needed < 0:
				# Increment back towards 0
				self.virtual_locks_needed += 1
				# Launch a new ball since the current one is locked.
				self.launch_ball(1)
				# See if finished re-locking
				if self.virtual_locks_needed == 0:
					self.disable_lock()
			else:	
				# Start multiball with the 4th lock
				if self.num_balls_locked == 4:
					if self.deadworld_mod_installed:
						self.game.deadworld.eject_balls(4)
						self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=4, time=25, now=True, allow_multiple_saves=True)
					else:
						self.launch_ball(3)
						self.enable_ball_save_after_launch=True
						self.delay(name='stop_globe', event_type=None, delay=7.0, handler=self.stop_globe)
					self.num_balls_locked = 0
					self.state = 'multiball'
					self.game.lamps.gi04.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
					self.display_text("Multiball!")
				# When not yet multiball, launch a new ball each time
				# one is locked.
				elif self.deadworld_mod_installed:
					self.launch_ball(1)
				self.disable_lock()	
				# Reset the ramp count
				self.num_left_ramp_shots = 0
		else:
			if self.deadworld_mod_installed:
				self.game.deadworld.eject_balls(1)
		self.lock_lamps()

	def sw_leftRampExit_active(self,sw):
		#ignore slow moving balls that made it by the diverter
		if self.state == 'load':
			if not self.lock_enabled:
				# Prepare to lock
				if self.num_left_ramp_shots == 2:
					# Don't enable locks if doing virtual locks.
					if self.virtual_locks_needed == 0:
						self.enable_lock()
					self.num_left_ramp_shots += 1

				# Should only get here if doing virtual locks,
				# but check anyway.
				elif self.num_left_ramp_shots == 3:
					if self.virtual_locks_needed > 0:
						self.num_balls_locked += 1
						self.virtual_locks_needed -= 1
						self.num_left_ramp_shots = 0
				else:
					self.num_left_ramp_shots += 1

			self.lock_lamps()

	def lock_lamps(self):
		if self.state == 'load':
			if self.num_left_ramp_shots == 0:
				schedule = 0x0000ffff
			elif self.num_left_ramp_shots == 1:
				schedule = 0x00ff00ff
			elif self.num_left_ramp_shots == 2:
				schedule = 0xf0f0f0f0
			else:
				schedule = 0xaaaaaaaa
			if self.num_balls_locked == 0:
				self.game.lamps.lock1.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock2.disable()
				self.game.lamps.lock3.disable()
			elif self.num_balls_locked == 1:
				self.game.lamps.lock1.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock3.disable()
			elif self.num_balls_locked == 2:
				self.game.lamps.lock1.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock3.schedule(schedule=schedule, cycle_seconds=0, now=True)
			elif self.num_balls_locked == 3:
				self.game.lamps.lock1.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock3.schedule(schedule=schedule, cycle_seconds=0, now=True)
		else:
			self.game.lamps.lock1.disable()
			self.game.lamps.lock2.disable()
			self.game.lamps.lock3.disable()

	def launch_ball(self, num):
		print "Launching Ball"
		self.game.coils.trough.pulse(20)
		num -= 1
		if num > 0:
			self.delay(name='launch', event_type=None, delay=2.0, handler=self.launch_ball, param=num)
		else:
			if self.enable_ball_save_after_launch:
				self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=4, time=25, now=False, allow_multiple_saves=True)
				self.enable_ball_save_after_launch = False
			

	def how_many_balls_locked(self):
		return self.num_balls_locked

	def stop_globe(self):
		self.game.deadworld.mode_stopped()
		
	
