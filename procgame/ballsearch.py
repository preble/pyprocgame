from game import *
from dmd import *

class BallSearch(Mode):
	"""Ball Search mode."""
	def __init__(self, game, priority, countdown_time, reset_switch_names, disable_switch_names=[], enable_switch_names=[], coils=[], special_handler_modes=[]):
		self.disable_switch_names = disable_switch_names
		self.countdown_time = countdown_time
		self.coils = coils
		self.special_handler_modes = special_handler_modes
		Mode.__init__(self, game, 8)
		for switch in reset_switch_names:
			self.add_switch_handler(name=switch, event_type='open', delay=None, handler=self.reset)
		# The disable_switch_names identify the switches that, when closed, 
		# keep the ball search from occuring.  This is typically done, 
		# for instance, when a ball is in the shooter lane or held on a flipper.
		for switch in disable_switch_names:
			self.add_switch_handler(name=switch, event_type='closed', delay=None, handler=self.stop)

	#def sw_trough1_open_for_200ms(self, sw):
	#	if self.game.is_trough_full():
	#		for special_handler_mode in self.special_handler_modes:
	#			special_handler_mode.mode_stopped()
	#		self.stop(0)

        def reset(self,sw):
		schedule_search = 1
		for switch in self.disable_switch_names:
			if self.game.switches[switch].is_closed():
				schedule_search = 0

		if schedule_search:
			self.cancel_delayed(name='ball_search_countdown');
			self.delay(name='ball_search_countdown', event_type=None, delay=self.countdown_time, handler=self.perform_search, param=0)

        def stop(self,sw):
		self.cancel_delayed(name='ball_search_countdown');

	def perform_search(self, completion_wait_time, completion_handler = None):
		if (completion_wait_time != 0):
			self.game.set_status("Balls Missing") # Replace with permanent message
		delay = .150
		for coil in self.coils:
			self.delay(name='ball_search_coil1', event_type=None, delay=delay, handler=self.pop_coil, param=coil)
			delay = delay + .150
		for special_handler_mode in self.special_handler_modes:
			self.game.modes.add(special_handler_mode)
			self.delay(name='remove_special_handler_mode', event_type=None, delay=7, handler=self.remove_special_handler_mode, param=special_handler_mode)
			delay = delay + .150

		if (completion_wait_time != 0):
			#self.delay(name='search_completion', event_type=None, delay=completion_wait_time, handler=completion_handler, param=completion_param)
			pass
		else:
			self.cancel_delayed(name='ball_search_countdown');
			self.delay(name='ball_search_countdown', event_type=None, delay=self.countdown_time, handler=self.perform_search, param=0)
	
	def pop_coil(self,coil):
		coil.pulse()

	def remove_special_handler_mode(self,special_handler_mode):
		self.game.modes.remove(special_handler_mode)
