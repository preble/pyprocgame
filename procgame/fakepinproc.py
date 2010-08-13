import time
import pinproc

class FakePinPROC(object):
	"""Stand-in class for :class:`pinproc.PinPROC`.  Generates DMD events."""
	
	last_dmd_event = 0
	
	frames_per_second = 60
	"""Frames per second at which to dispatch :attr:`pinproc.EventTypeDMDFrameDisplayed` events."""
	
	def __init__(self, machine_type):
		pass
	def noop(self, *args, **kwargs):
		pass
	def switch_get_states(self, *args):
		return [pinproc.EventTypeSwitchOpenDebounced] * 256
	def get_events(self):
		events = []
		now = time.time()
		seconds_since_last_dmd_event = now - self.last_dmd_event
		missed_dmd_events = min(int(seconds_since_last_dmd_event*float(self.frames_per_second)), 16)
		if missed_dmd_events > 0:
			self.last_dmd_event = now
			events.extend([{'type':pinproc.EventTypeDMDFrameDisplayed, 'value':0}] * missed_dmd_events)
		return events
	def __getattr__(self, name):
		if name == 'get_events':
			return self.get_events
		elif name == 'switch_get_states':
			return self.switch_get_states
		else:
			return self.noop
