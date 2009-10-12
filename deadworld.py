import procgame
from procgame import *

class Deadworld(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, deadworld_mod_installed):
		super(Deadworld, self).__init__(game, priority)
		self.deadworld_mod_installed = deadworld_mod_installed
		self.lock_enabled = 0
		self.num_balls_locked = 0
		self.num_player_balls_locked = 0
		self.num_balls_to_eject = 0
		self.ball_eject_in_progress = 0
		self.performing_ball_search = 0
		self.add_switch_handler(name='globePosition2', event_type='active', delay=None, handler=self.crane_activate)
	
	def mode_started(self):
		pass

	def mode_stopped(self):
		self.game.coils.globeMotor.disable()

	def initialize(self, lock_enabled=0, num_player_balls_locked=0):
		self.lock_enabled = lock_enabled
		self.num_player_balls_locked = num_player_balls_locked
		if (self.lock_enabled or self.num_balls_locked > 0):
			self.game.coils.globeMotor.pulse(0)

	def enable_lock(self):
		self.lock_enabled = 1
		self.game.coils.globeMotor.pulse(0)

	def disable_lock(self):
		self.lock_enabled = 0

	def sw_leftRampToLock_active(self, sw):
		if self.deadworld_mod_installed:
			self.num_balls_locked += 1
			self.game.set_status("balls locked: " + str(self.num_balls_locked))

	def eject_balls(self,num):
		if not self.num_balls_to_eject:
			self.perform_ball_eject()
		self.num_balls_to_eject += num
		self.ball_eject_in_progress = 1
		
	def perform_ball_search(self):
		self.performing_ball_search = 1
		self.perform_ball_eject()
		self.ball_eject_in_progress = 1

	def perform_ball_eject(self):
		self.game.coils.globeMotor.pulse(0)
		if self.deadworld_mod_installed:
			switch_num = self.game.switches['globePosition2'].number
			self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, True)

	def sw_craneRelease_active(self,sw):
		if not self.performing_ball_search:
			self.num_balls_to_eject -= 1
			self.num_balls_locked -= 1
			self.game.set_status("1balls locked: " + str(self.num_balls_locked))
		else:
			self.performing_ball_search = 0
			self.game.set_status("2balls locked: " + str(self.num_balls_locked))
			
		
	def sw_magnetOverRing_open(self,sw):
		if self.ball_eject_in_progress:
			self.game.coils.craneMagnet.pulse(0)
			self.delay(name='crane_release', event_type=None, delay=2, handler=self.crane_release)

	def crane_release(self):
		self.game.coils.crane.disable()
		self.game.coils.craneMagnet.disable()
		self.delay(name='crane_release_check', event_type=None, delay=1, handler=self.crane_release_check)


	def crane_release_check(self):
		if self.num_balls_to_eject > 0:
			self.perform_ball_eject()
		else:
			if self.num_balls_locked > 0:
				self.game.coils.globeMotor.pulse(0)
			self.ball_eject_in_progress = 0
			switch_num = self.game.switches['globePosition2'].number
			self.game.install_switch_rule_coil_disable(switch_num, 'closed_debounced', 'globeMotor', True, False)

	def crane_activate(self,sw):
		if self.ball_eject_in_progress:
			self.game.coils.crane.pulse(0)

	def get_num_balls_locked(self):
		return self.num_balls_locked - self.num_balls_to_eject

#	def mode_tick(self):
#		self.game.set_status(str(self.num_balls_locked))
