import time
import pinproc
import Queue
from game import gameitems

class FakePinPROC(object):
	"""Stand-in class for :class:`pinproc.PinPROC`.  Generates DMD events."""
	
	last_dmd_event = 0
	
	frames_per_second = 60

	drivers = gameitems.AttrCollection()

	switch_events = []
	switch_rules = [{'notifyHost':False, 'drivers':[]}] * 1024
	"""List of events"""

	"""Frames per second at which to dispatch :attr:`pinproc.EventTypeDMDFrameDisplayed` events."""
	
	def __init__(self, machine_type):
		# Instantiate 256 drivers.
		for i in range(0, 256):
			name = 'driver' + str(i)
			self.drivers.add(name, gameitems.AuxDriver(self, name, i, True))

	def noop(self, *args, **kwargs):
		""" Empty method used when no virtual equivalent to a pypinproc method is necessary.  This allows a game to switch back and forth between pypinproc and this fakepinproc class without modification. """
		pass

	def switch_get_states(self, *args):
		""" Method to provide default switch states. """
		return [0] * 256

	def get_events(self):
		""" Get all switch and DMD events since the last time this was called. """
		events = []
		events.extend(self.switch_events)
		self.switch_events = []
		now = time.time()
		seconds_since_last_dmd_event = now - self.last_dmd_event
		missed_dmd_events = min(int(seconds_since_last_dmd_event*float(self.frames_per_second)), 16)
		if missed_dmd_events > 0:
			self.last_dmd_event = now
			events.extend([{'type':pinproc.EventTypeDMDFrameDisplayed, 'value':0}] * missed_dmd_events)
		return events

	def driver_pulse(self, number, milliseconds):
		""" Send a pulse command to a virtual driver. """
		self.drivers[number].pulse(milliseconds)

	def driver_schedule(self, number, schedule, cycle_seconds, now):
		""" Send a schedule command to a virtual driver. """
		self.drivers[number].schedule(schedule, cycle_seconds, now)

	def driver_disable(self, number):
		""" Send a disable command to a virtual driver. """
		self.drivers[number].disable()

	# There is no state structure for virtual drivers.  Just return
	# the number since it's typically stored in the structure.
	def driver_get_state(self, number):
		""" Returns needed elements of a virtual drivers state structure.  In pypinproc, the structure matches the attributes of a driver in the P-ROC.  The concept of the structure can be very simple here.  For now it just represents the driver number. """
		return number

	# Switch rule methods
	def switch_update_rule(self, num, state, rule_params, drivers):
		""" Stores P-ROC switch rules in an internal switch_rules list. """
		# Convert the pyprocgame event name to a pinproc event.
		if state == 'closed_debounced': 
			pr_state = pinproc.EventTypeSwitchClosedDebounced
		elif state == 'open_debounced': 
			pr_state = pinproc.EventTypeSwitchOpenDebounced
		elif state == 'closed_nondebounced': 
			pr_state = pinproc.EventTypeSwitchClosedNondebounced
		else: pr_state = pinproc.EventTypeSwitchOpenNondebounced

		# Find the appropriate switch rule entry to overwrite
		rule_index = ((pr_state-1) * 256) + num
		notify = rule_params['notifyHost']
		# Copy the list so that unique driver lists are stored
		# in each switch rule entry.
		driverlist = list(drivers)

		# Overwrite the existing rule with this new one.
		self.switch_rules[rule_index] = {'notifyHost':notify, 'drivers':driverlist}
		return True

	def add_switch_event(self, number, event_type):
		""" Called by the simulating element to send in a switch event. """

		# Event types start at 1; so use it to figure out in which
		# 256 rule block to find the rule for this event.
		rule_index = ((event_type-1) * 256) + number

		# If the event says to notify host, add it to the list
		# of pending events.
		if self.switch_rules[rule_index]['notifyHost']:
			event = {'type':event_type, 'value':number}
			self.switch_events.append(event)

		# Now see if the switch rules indicate one or more drivers
		# needs to change.
		drivers = self.switch_rules[rule_index]['drivers']
		for driver_rule in drivers:
			if 'pulse' in driver_rule[0]:
				self.drivers[driver_rule[1][0]].pulse(driver_rule[1][1])
			elif 'disable' in driver_rule[0]:
				self.drivers[driver_rule[1][0]].disable()
			elif 'schedule' in driver_rule[0]:
				self.drivers[driver_rule[1][0]].schedule(driver_rules[1][1], driver_rules[1][2], driver_rules[1][3])


	def watchdog_tickle(self):
		""" This method contains things that need to happen every iteration of a game's runloop. """
		for driver in self.drivers: driver.tick()

	def __getattr__(self, name):
		if name == 'get_events':
			return self.get_events
		elif name == 'switch_get_states':
			return self.switch_get_states
		else:
			return self.noop
