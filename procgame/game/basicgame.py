from . import GameController
from ..dmd import DisplayController, font_named
from ..modes import ScoreDisplay
from .. import config
from .. import auxport
from .. import alphanumeric
import pinproc
import time
import datetime
import traceback

class BasicGame(GameController):
	""":class:`BasicGame` is a subclass of :class:`~procgame.game.GameController` 
	that includes and configures various useful helper classes to provide:
	
	* A :class:`~procgame.modes.ScoreDisplay` mode/layer at priority 1, available
	  at ``self.score_display``.
	* A :class:`~procgame.dmd.DisplayController` mode to manage the DMD layers,
	  at ``self.dmd``.
	* A :class:`~procgame.desktop.Desktop` helper at ``self.desktop`` configured 
	  to display the most recent DMD frames on the desktop, as well as interpret
	  keyboard input as switch events.
	
	It is a recommended base class to build your game upon, or use as a template
	if your game has special requirements.
	"""
	
	dmd = None
        alpha_display = None
	score_display = None
        aux_port = None
	desktop = None
	
	def __init__(self, machine_type):
		super(BasicGame, self).__init__(machine_type)

		self.aux_port = auxport.AuxPort(self)
		if self.machine_type == pinproc.MachineTypeWPCAlphanumeric:
			self.alpha_display = alphanumeric.AlphanumericDisplay(self.aux_port)
		else:
			self.dmd = DisplayController(self, width=128, height=32, message_font=font_named('Font07x5.dmd'))
		self.score_display = ScoreDisplay(self, 0)

		
		use_desktop = config.value_for_key_path(keypath='use_desktop', default=True)
		if use_desktop: 
			import procgame.desktop
			from ..desktop import Desktop
			self.desktop = Desktop()

		if self.dmd: self.dmd.frame_handlers.append(self.set_last_frame)

	def load_config(self, path):
		super(BasicGame,self).load_config(path)
		
		# Setup the key mappings from the config.yaml.
		# We used to do this in __init__, but at that time the
		# configuration isn't loaded so we can't peek into self.switches.
		key_map_config = config.value_for_key_path(keypath='keyboard_switch_map', default={})
		if self.desktop:
			for k, v in key_map_config.items():
				switch_name = str(v)
				if self.switches.has_key(switch_name):
					switch_number = self.switches[switch_name].number
				else:
					switch_number = pinproc.decode(self.machine_type, switch_name)
				self.desktop.add_key_map(ord(str(k)), switch_number)

	def reset(self):
		"""Calls super's reset and adds the :class:`ScoreDisplay` mode to the mode queue."""
		super(BasicGame, self).reset()
		self.modes.add(self.score_display)
		
	def dmd_event(self):
		"""Updates the DMD via :class:`DisplayController`."""
		if self.dmd: self.dmd.update()
	
	def get_events(self):
		"""Overriding GameController's implementation in order to append keyboard events."""
		events = super(BasicGame, self).get_events()
		if self.desktop: events.extend(self.desktop.get_keyboard_events())
		return events
	
	def tick(self):
		"""Called once per run loop.
		
		Displays the last-received DMD frame on the desktop."""
		super(BasicGame, self).tick()
		self.show_last_frame()

	def score(self, points):
		"""Convenience method to add *points* to the current player."""
		p = self.current_player()
		p.score += points

	#
	# Support for showing the last DMD frame on the desktop.
	#
	#   Because showing each frame on the desktop can be pretty time-consuming,
	#   we show it only once per run loop cycle (via tick()), and only when there
	#   is a new frame (via last_frame).  By showing it this way (and not directly
	#   from DisplayController's frame_handlers), we allow the run loop to progress
	#   quickly without getting bogged down drawing the DMD on the desktop if a 
	#   large number of DMD events arrive 'at once'.
	#
	
	last_frame = None
	
	def set_last_frame(self, frame):
		self.last_frame = frame
	
	def show_last_frame(self):
		if self.desktop and self.last_frame:
			self.desktop.draw(self.last_frame)
			self.last_frame = None

class BasicRecordableGame(BasicGame):
	"""RecordableGameController provides the ability to record all switch events to a
	simulation file. The simulation file can then be played back using fakePinPROC in
	order to reproduce events or develop code further.
	"""
	_switch_record_file = None
	_start_time = 0
	_is_currently_recording = False
	
	def __init__(self, machine_type):
		super(BasicRecordableGame, self).__init__(machine_type)
			
		# Mark down our start time so we get relative simulator timestamps when recording events
		self._start_time = (time.time() * 1000)
		
		
	def start_recording(self):
		""" Grabs the current switch matrix state snapshot and begins recording
		    switch events starting at simulator time zero (0)
		"""
		# Grab the current timestamp and key the switch record file off of that timestamp
		current_time = datetime.datetime.now()
		timestamp = current_time.strftime("%Y-%m-%d-%H%M")
		# Open the switch record file for writing.
		# Note, we don't close it until after the game loop exits
		self._switch_record_file = open("switch-record-"+timestamp+".txt", 'w')
		
		# Grab switch matrix snapshot and write it to the file
		self.take_switch_snapshot()
		
		self._is_currently_recording = True
		self.logger.info("Recording Started")
		
	def stop_recording(self):
		""" Stops a currently recording switch file and closes it """
		self._is_currently_recording = False
		self._switch_record_file.close()
		self.logger.info("Recording Stopped")
		
	def is_recording(self):
		return self._is_currently_recording;
	
	def take_switch_snapshot(self):
		""" Iterates through the entire switch matrix and writes the states of all switches
		    into the switch record file.
		"""
		states = self.proc.switch_get_states()
		for sw in self.switches:
			self._switch_record_file.write(str(sw.number) + "|" + str(states[sw.number]) + "\n")
		
	def process_event(self, event):
		""" Called each time an event happens on the machine. This is where
		    we intercept switch state changes and write them to a file before
		    passing them down the mode queue
		"""
		event_type = event['type']
		event_value = event['value']
		if event_type == 99: # CTRL-C to quit
			print "CTRL-C detected, quiting..."	
			self.end_run_loop()
		elif event_type == pinproc.EventTypeDMDFrameDisplayed: # DMD events
			#print "% 10.3f Frame event.  Value=%x" % (time.time()-self.t0, event_value)
			self.dmd_event()
		else:
			try:
				sw = self.switches[event_value]
				if 'time' in event:
					sw.hw_timestamp = event['time']
			except KeyError:
				self.logger.warning("Received switch event but couldn't find switch %s." % event_value)
				return
			
			if sw.debounce:
				recvd_state = event_type == pinproc.EventTypeSwitchClosedDebounced
			else:
				recvd_state = event_type == pinproc.EventTypeSwitchClosedNondebounced

			# If we're recording, write the switch event to our file
			if self.is_recording():
				self.write_event_to_file(event,sw.name)

			if sw.state != recvd_state:
				sw.set_state(recvd_state)
				self.logger.info("%s:\t%s\t(%s)", sw.name, sw.state_str(),event_type)
				self.modes.handle_event(event)
				
				sw.reset_timer()

	def write_event_to_file(self, event, friendly_switch_name = ""):
		""" Writes the specified event array to a switch record file """
		currentTime = (time.time() * 1000) - self._start_time
		eventStr = str(currentTime) + "|" + str(event['type']) + "|" + str(event['value']) + "|" + friendly_switch_name;
		if 'time' in event:
			eventStr = eventStr + "|" + str(event['time'])
		self._switch_record_file.write(eventStr+"\n")
		self.logger.info("%s:\tswitch recorded-\t%s",str(currentTime),friendly_switch_name)
		print event

	def run_loop(self, min_seconds_per_cycle=None):
		""" We override the original run loop to encapsulate it inside of a 
		try catch block. That way we don't have to constantly open/close switch report
		files at each event because that can be excessive. If we catch an exception, gracefully
		close the file.
		"""
		try:
			super(BasicRecordableGame,self).run_loop(min_seconds_per_cycle)
		except Exception as e:
			print e
			print traceback.format_exc()
			
		""" Close the switch record file """
		if self.is_recording():
			self._switch_record_file.close()

