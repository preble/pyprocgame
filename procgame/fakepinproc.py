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
			self.drivers.add(name, gameitems.VirtualDriver(None, name, i, True))
			
		

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

	def driver_get_state(self, number):
		""" Return the state dictionary for the specified driver. """
		return self.drivers[number].state

	# Switch rule methods
	def switch_update_rule(self, num, state, rule_params, drivers, drive_outputs_now=False):
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
			self.drivers[driver_rule['driverNum']].update_state(driver_rule)


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

class FakePinPROCPlayback(FakePinPROC):
	""" FakePinPROCPlayback offers the functionality to play back switch
	events from a switch record file taken from real gameplay.
	
	The class subclasses fakepinproc to maintain the same functionality and
	interop by simply changing the proc class in config.yaml
	"""
	
	_start_time = 0 # The simulator start time so we know how to calculate simulator time
	
	_playback_file = None # Playback file object that we read from
	
	_events = dict() # We store events in a dictionary keyed by their simulator time
	
	_event_timestamps = None # Event timestamps are stored in a list so they can be sorted so we access the dictionary in order.

	_states = [0] * 256 # Local switch state repository
	
	def __init__(self, machine_type):
		super(FakePinPROCPlayback, self).__init__(machine_type)
		
		self._states = [0] * 256 # Initialize all switch values to 0
		
		self._playback_file = open("playback.txt", 'r') # Open our playback file for reading
		self._parse_playback_file() # Parse the playback file to get our initial switch states and load all events into memory
		self._playback_file.close() # Close the playback file after reading into memory
		
		self._event_timestamps = self._events.keys() # Populate our list of timestamps from the events dictionary keys
		self._event_timestamps.sort() # Sort timestamps from least to greatest so we access all events in order
		
		
		self._start_time = (time.clock() * 1000) # Mark down the current start time so we know when to process an event
		
	def switch_get_states(self, *args):
		""" Method to provide current simulator switch states. """
		
		return self._states
		
	def get_events(self):
		# Populate the events list from our fakepinproc DMD events, etc
		events = super(FakePinPROCPlayback, self).get_events()
		# Mark down the current time so we can check whether or not we should fire an event yet
		current_time = self._get_current_simulator_time()

		# Loop through all events that we should execute now
		while len(self._event_timestamps) > 0 and self._event_timestamps[0] <= current_time:
			evt = self._events[self._event_timestamps[0]]
			print "[%s] [%s] Firing switch %s" % (str(current_time),str(self._event_timestamps[0]), evt['swname']) 
			# Add the event to the event queue
			events.append(evt)
			# Remove the already processed events from our data structures so we don't process them again
			del self._events[self._event_timestamps[0]]
			del self._event_timestamps[0]
			
		return events
			
		
	def _get_current_simulator_time(self):
		return (time.clock() * 1000) - self._start_time
		
	def _parse_playback_file(self):
		line = self._playback_file.readline()
		while line:
			line = line.strip()
			evt = line.split("|")
			if len(evt) == 2:
				# This is a switch state declaration
				swnum = int(evt[0])
				swval = int(evt[1])
				self._states[swnum] = swval
			elif len(evt) >= 4:
				# This is an actual event to schedule
				procEvent = dict()
				procEvent['type'] = int(evt[1])
				procEvent['value'] = int(evt[2])
				procEvent['swname'] = evt[3]
				if len(evt) >= 5:
					procEvent['time'] = evt[4]
				
				self._events[float(evt[0])] = procEvent
			
			line = self._playback_file.readline()

