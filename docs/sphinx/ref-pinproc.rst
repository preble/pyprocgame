************************
pinproc Module Reference
************************

.. module:: pinproc

The :mod:`pinproc` module enables control of the P-ROC hardware from within Python (using :class:`~pinproc.PinPROC`), as well as helper routines written in native code (C) to assist with tasks like DMD buffer manipulation.


PinPROC Class
=============

.. class:: pinproc.PinPROC(machine_type)

	Represents the P-ROC hardware interface.  This class is initialized with *machine_type*.  *machine_type* can be one of the :ref:`machine_type_constants` or, for compatibility, a string (wpc, wpc95, wpcAlphanumeric, sternSAM, sternWhitestar, or custom).  The machine type is used for the initial configuration of the P-ROC hardware interface.
	
	An ``IOError`` is raised if the P-ROC device cannot be found.  A ``ValueError`` is raised if *machine_type* is invalid.
	
	.. note:: All I/O between the software and the P-ROC hardware is buffered to ensure maximum USB throughput.  This means that driver update commands are only sent to the hardware when the software buffer is full, or when :meth:`flush` is called.  If you are using the :class:`procgame.game.GameController` run loop you do not need to manually flush the buffers, as they are flushed after every run loop cycle.


	.. method:: aux_send_commands(address, aux_commands)
	
		Writes *aux_commands* (a list of commands) to the P-ROC’s auxiliary bus instruction memory, starting at *address*, which is an offset into the instruction memory.
		
		See :ref:`aux-command-functions` and :ref:`aux-bus-programming` for more on the auxiliary bus.
	
	.. method:: dmd_draw(data)
	
		Displays *data* on the dot matrix display, which may be a :class:`DMDBuffer` (recommended) or a string (not recommended).
		
		A :class:`DMDBuffer` is interpreted as a 128x32 8-bits-per-pixel 16-color (``0x0`` thru ``0xF``) image.  Each pixel value is mapped using the mapping described in :meth:`set_dmd_color_mapping`.  A ``ValueError`` is raised if the buffer is not 128x32.
		
		If a string is passed it will be interpreted as a 128x32 image with raw 32-bits-per-pixel 8-bits-per-channel pixel data.  The channels of each pixel are summed and then divided to derive a 4-color image.
		
		If the DMD has not been previously configured using :meth:`dmd_update_config` it will be configured with the default settings prior to updating the display.
	
	.. method:: dmd_update_config(high_cycles=None)
	
		Configures the DMD using defaults except where specified otherwise.
		
		*high_cycles* is optional.  If supplied it must be a sequence of 4 integers representing the ``high_cycles`` values for the display.  These values affect the timing of the display (frames per second) as well as the brightness of the dots.
	

	.. method:: driver_disable(number)

		Disables (de-energizes) the specified driver *number*.


	.. method:: driver_pulse(number, milliseconds)
	
		Pulses driver *number* for the specified number of *milliseconds*.  0 indicates forever; the maximum is 255.
	
	
	.. method:: driver_schedule(number, schedule, cycle_seconds, now)
	
		Turns on/off the specified driver *number* according to the schedule.

		*schedule* is a 32-bit mask where each bit corresponds to a 1/32 of a second timeslot.  Active bits identify timeslots during which the driver number should be on.  The least significant bit corresponds to the first timeslot.

		The schedule is driven for the specified number of *cycle_seconds*, 0 = forever, max 255.

		*now* determines whether the schedule is activated immediately (``True``) or if it is synchronized to a 1 second timer internal to the P-ROC (``False``).  When ``now = False`` is used with multiple drivers, the schedules of all of the drivers will be synchronized.
	
	
	.. method:: driver_patter(number, milliseconds_on, milliseconds_off, original_on_time)
	
		Drives the specified driver *number* with an indefinite pitter-patter sequence, where the driver is repeatedly turned on for *milliseconds_on* and the off for *milliseconds_off*, each with a max of 127.

		If *original_on_time* is non-zero, the driver is first pulsed for that number of milliseconds before the pitter-patter sequence begins, with a max 255.

		Pitter-patter sequences are commonly used for duty cycle control of driver circuits.  A case where *original_on_time* might be non-zero would be for a single coil flipper circuit that needs to be driven to activate the flipper before the pitter-patter sequence is used to hold the flipper up.

	
	.. method:: driver_pulsed_patter(number, milliseconds_on, milliseconds_off, milliseconds_overall_patter_time)
	
		Drives the specified driver *number* with a timed pitter-patter sequence, where the driver is repeatedly turned on for *milliseconds_on* and then off for *milliseconds_off*, each with a max of 127.  

		The driver is disabled after *milliseconds_overall_patter_time*, max 255.
	
	
	.. method:: driver_get_state(number)
	
		Returns a dictionary containing the state information for the specified driver.  See :ref:`driver-state-dict` for a description of the dictionary.
	
	.. method:: driver_update_global_config(enable_outputs, global_polarity,use_clear,strobe_start_select,start_strobe_time,matrix_row_enable_index_0, matrix_row_enable_index_1, active_low_matrix_rows, tickle_stern_watchdog, encode_enables, watchdog_expired, watchdog_enable, watchdog_reset_time)
	
		``enable_outputs``
			bool
		
		``global_polarity`` 
			bool 
		
		``use_clear`` 
			bool, ignored by the hardware.
		
		``strobe_start_select``
			bool - use external strobe to start driver update loop. Ignored by the hardware.
		
		``start_strobe_time`` 
			bool - driver update loop time.  Ignored by the hardware.
		
		``matrix_row_enable_index_0`` 
			int
		
		``matrix_row_enable_index_1`` 
			int
		
		``active_low_matrix_rows`` 
			bool
		
		``tickle_stern_watchdog`` 
			bool
		
		``encode_enables`` 
			bool - use muxed enables or individual lines.
		
		``watchdog_expired`` 
			bool 
		
		``watchdog_enable`` 
			bool
		
		``watchdog_reset_time`` 
			int - milliseconds

	.. method:: driver_update_group_config(group_num, slow_time, enable_index, row_activate_index, row_enable_select, matrixed, polarity, active, disable_strobe_after)
	
		``group_num`` 
			int
		
		``slow_time`` 
			int - milliseconds to keep each group active matrix - only.
		
		``enable_index`` 
			int - enable index to use for each group of data.
		
		``row_activate_index`` 
			int - data bit to enable for the group's row - matrix only.
		
		``row_enable_select`` 
			int - which of the 2 global matrix_row_enable_indexes to which to send the row_activate_index - matrix only
		
		``matrixed`` 
			bool
		
		``polarity`` 
			bool - takes precedence over global polarity.

		``active`` 
			bool - enables the group.
		
		``disable_strobe_after`` 
			bool - set if the data should be disabled after it has been driven - used mostly with matrix groups.
		
	
	.. method:: driver_update_state(dict)
	
		Updates a driver configuration using the passed dictionary.  The driver number is contained within the dictionary.  See :ref:`driver-state-dict` for a description of the dictionary.
	
	.. method:: flush()
	
		Writes all buffered commands to the P-ROC hardware.  This method is necessary because the internal command buffer is written to hardware only when it is full.
		
		**Why do the driver commands not flush themselves?**
		
		In order to maximize USB efficiency this method should be called only when necessary.  For example, the :class:`procgame.game.GameController` class's run loop only calls this method once per loop.
	
	.. method:: get_events()
	
		Returns a list of dictionaries representing P-ROC events.  Each dictionary contains a ``type`` key and a ``value`` key.  Event types include:
		
		+------+----------------------------------------------------------------------------------------+
		| Type | Meaning                                                                                |
		+======+========================================================================================+
		| 1    | The switch has changed from open to closed and the signal has been debounced.          |
		+------+----------------------------------------------------------------------------------------+
		| 2    | The switch has changed from closed to open and the signal has been debounced.          |
		+------+----------------------------------------------------------------------------------------+
		| 3    | The switch has changed from open to closed and the signal has not been debounced.      |
		+------+----------------------------------------------------------------------------------------+
		| 4    | The switch has changed from closed to open and the signal has not been debounced.      |
		+------+----------------------------------------------------------------------------------------+
		| 5    | A new frame has been displayed on the DMD and there is room in the buffer for another. |
		+------+----------------------------------------------------------------------------------------+
		
		This module provides constants for these values; see :ref:`event_type_constants`.  Switch-related event types contain the switch number as the ``value``.
	
	.. method:: reset(resetFlags)
	
		Resets the P-ROC interface to its defaults.  *resetFlags* has two possible values:
		
		+---+------------------------------------------------------------------------------+
		| 0 | Resets the software only.                                                    |
		+---+------------------------------------------------------------------------------+
		| 1 | Resets the software to its defaults and applies the changes to the hardware. |
		+---+------------------------------------------------------------------------------+
	
	
	.. method:: set_dmd_color_mapping(mapping)
	
		Assigns the color mapping that is used by :meth:`dmd_draw`.  *mapping* must be a sequence of 16 integer values.  These values are initially set to 0..15, but can be modified to affect the contrast of the display and compensate for brightness differences.  Unlike :meth:`dmd_update_config` these values do not affect the timing of the display.
	
	
	.. method:: switch_get_states()
	
		Returns a list of integers representing the last known state of each switch.  See the table in :meth:`get_events` for a list of state values.
	
	
	.. method:: switch_update_rule(number, event_type, rule, linked_drivers)
	
		Configures the rule for the given switch *number* when its state changes to *event_type*.
		Rules are used to configure automatic hardware actions in response to switch events.
		Actions include notifying the host and changing driver states.
		
		*event_type* is one of: ``'closed_debounced'``, ``'open_debounced'``, ``'closed_nondebounced'`` or ``'open_nondebounced'``.
		
		*rule* is a dictionary with keys ``'notifyHost'`` and ``'reloadActive'``, both with integer values.  If ``'notifyHost'`` is ``True`` a switch event will be received via :meth:`get_events` when this rule is triggered.  If ``'reloadActive'`` is ``True`` a 125ms reload timer will be set on this rule which will prevent it from re-driving any associated drivers repeatedly if the switch activates repeatedly.
		
		*linked_drivers* is a list of driver state dictionaries, which may be constructed with :ref:`driver-state-functions`.
	
	
	.. method:: watchdog_tickle()
	
		This method resets the hardware watchdog timer.  The timer should be tickled regularly, as the drivers are disabled when the watchdog timer expires.  The default watchdog timer period is 1 second.
	
	.. method:: write_data(module, address, data)
	
		``module``
			P-ROC FPGA module number
	
		``address``
			P-ROC FPGA Register address

		``data``
			32-bit data


Functions, Constants, and Data Structures
=========================================

.. _driver-state-functions:

Driver State Functions
----------------------

The following functions each take a driver state dictionary (:ref:`ref <driver-state-dict>`) and zero or more parameters describing how to modify the dictionary.  The modified copy is returned by the function.  These functions are designed to facilitate configuring switch rules with :meth:`PinPROC.switch_update_rule`.  

.. function:: driver_state_disable(state)

	Corresponds to :meth:`PinPROC.driver_disable`.

.. function:: driver_state_pulse(state, milliseconds)

	Corresponds to :meth:`PinPROC.driver_pulse`.

.. function:: driver_state_schedule(state, schedule, seconds, now)

	Corresponds to :meth:`PinPROC.driver_schedule`.

.. function:: driver_state_patter(state, milliseconds_on, milliseconds_off, original_on_time)

	Corresponds to :meth:`PinPROC.driver_patter`.

.. function:: driver_state_pulsed_patter(state, milliseconds_on, milliseconds_off, milliseconds_overall_patter_time)

	Corresponds to :meth:`PinPROC.driver_pulsed_patter`.


.. _driver-state-dict:

Driver State Dictionary
-----------------------

======================== ==================================
  Key                      Meaning
======================== ==================================
``driverNum``            Hardware driver number.
``outputDriveTime``      Output drive time., 0-255.
``polarity``             Polarity of the driver.
``state``                On or off: 1 or 0.
``waitForFirstTimeSlot`` 1 instructs P-ROC to wait for the next time slot.
``timeslots``            32-bit driver schedule.
``patterOnTime``         0-127.
``patterOffTime``        0-127.
``patterEnable``         0 or 1 to enable patter behavior.
======================== ==================================


.. _event_type_constants:

Event Type Constants
--------------------

.. attribute:: EventTypeSwitchClosedDebounced

.. attribute:: EventTypeSwitchOpenDebounced

.. attribute:: EventTypeSwitchClosedNondebounced

.. attribute:: EventTypeSwitchOpenNondebounced

.. attribute:: EventTypeDMDFrameDisplayed


.. _machine_type_constants:

Machine Type Constants
----------------------

.. attribute:: MachineTypeWPC
.. attribute:: MachineTypeWPC95
.. attribute:: MachineTypeWPCAlphanumeric
.. attribute:: MachineTypeSternSAM
.. attribute:: MachineTypeSternWhitestar
.. attribute:: MachineTypeCustom


.. _aux-command-functions:

Auxiliary Command Functions
---------------------------

Auxiliary bus commands provide a way to control auxiliary bus devices, like alphanumeric displays or custom displays found on various playfields.  When written to the P-ROC using :meth:`~pinproc.PinPROC.aux_send_commands`, commands are stored in a 256-entry memory from which they are executed in a manner similar to a microcontroller executing commands stored in an instruction memory.

Auxiliary bus devices are typically hung off of the standard multiplexed data bus that connects the P-ROC to a machine’s Power/Driver board.  They therefore receive data from the data bus only when the associated enable lines are driven.  The auxiliary bus commands are therefore made up of both data and enables.  See :ref:`aux-bus-programming` for more.

The following helper functions assist with creating aux commands:

.. function:: aux_command_output_custom(data, extra_data, enables, mux_enables)

	Drives *data and *extra_data* onto the P-ROC’s multiplexed data bus.

	*enables* identifies the enable line to activate with the data, and *mux_enables* determines whether the enable line is driven directly (WPC machines) or multiplexed (Stern machines).

	The *extra_data* lines on the P-ROC are shared with the dot-matrix-display control signals and will only work when *machine_type* is :attr:`MachineTypeWPCAlphanumeric`.


.. function:: aux_command_output_primary(data, extra_data)

	Drives *data* and *extra_data* to the primary auxiliary bus device.  

	On :attr:`MachineTypeWPCAlphanumeric` machines, the primary auxiliary bus enable is 8.
	On :attr:`MachineTypeSternWhitestar` and :attr:`MachineTypeSternSAM` machines, the primary auxiliary bus enable is 6.

.. function:: aux_command_output_secondary(data, extra_data)

	Drives *data* to the secondary auxiliary bus device.  *extra_data* is unused.

	There is no secondary auxiliary bus enable on :attr:`MachineTypeWPCAlphanumeric` machines.
	On :attr:`MachineTypeSternWhitestar` and :attr:`MachineTypeSternSAM` machines, the secondary auxiliary bus enable is 11.


.. function:: aux_command_delay(delay_time)

	Tells the auxiliary bus logic to wait for *delay_time* microseconds. Max *delay_time* is 16383.  For longer delays, consecutive delay commands can be used.


.. function:: aux_command_jump(address)

	Tells the auxiliary bus logic to jump to the specified *address* in the auxiliary bus instruction memory.


.. function:: aux_command_disable()

	Deactivates the command.  When the auxiliary bus logic reads an inactive command, it will do nothing until the command is overwritten with an active command.


Other Functions
---------------

.. function:: decode(machine_type, number)

	Converts a string (*number*) describing a coil, lamp, switch, or GI string into an integer P-ROC driver number.
	This allows coils and switches to be specified (for example in a YAML file) in a format that corresponds to the
	printed manual numbering and not to the actual P-ROC hardware coil or switch.
	
	The following formats are accepted: ``Cxx`` (coil), ``Lxx`` (lamp), ``Sxx`` (matrix switch), ``SFx`` (flipper grounded switch), or ``SDx`` (dedicated grounded switch).
	
	If the string does not match this format it will be converted directly into an integer.


DMDBuffer Class
===============

.. class:: pinproc.DMDBuffer(width, height)
	
	Buffer of dots.  Initializes the buffer with a size of `width` x `height`.
	
	A dot is 8 bits/1 byte in size and can have a value between 0 and 255 (0xff).  Thus a ``DMDBuffer`` can be used to store arbitrary values (and is in the case of :class:`procgame.dmd.Font`, which uses one buffer to store font character widths).  However, drawing-oriented functions such as :meth:`.copy_to_rect` assume that the maximum value for a dot is 15 (0xf).
	
	.. method:: clear()
	
		Fills the entire buffer with black dots.
	
	.. method:: copy_to_rect(dst, dst_x, dst_y, src_x, src_y, width, height, op='copy')
	
		Copies dots from this instance of ``DMDBuffer`` to ``dst``, another ``DMDBuffer``.  The source rectangle has its origin at (``src_x``, ``src_y``) and its size is ``width`` x ``height``.  It is copied to a rectangle in the ``dst`` buffer with its origin at (``dst_x``, ``dst_y``).  
		
		``copy_to_rect()`` will adjust the rectangle to fit within the bounds of the source buffer, and will only copy those dots that would be within the bounds at the destination.  This allows negative (out of bounds) origins to be used for the developer's convenience.
		
		The ``op`` parameter, or operation, describes how the dots are gathered and applied.  The following are valid ``op`` parameter values (all are strings):
		
		``'copy'``
			Copies dots from the source to the destination.
		``'add'``
			Adds the value of the source dot to that of the destination dot.  The result is capped at 15 (0xf).
		``'sub'``
			Subtracts the value of the source dot from the destination dot.  The result will have a minimum value of 0.
		``'blacksrc'``
			Like copy, except it only copies the dot from source to destination if the destination dot is non-zero.  This allows for primitive alpha channels.
	
	.. method:: fill_rect(x, y, width, height, value)
	
		Fills the rectangle in this buffer described by origin ``x``, ``y`` with size ``width`` x ``height`` with dot value ``value``.
	
	.. method:: get_data()
	
		Returns the contents of the buffer as a string of length ``width`` x ``height``.
	
	.. method:: get_dot(x, y)
	
		Returns the dot value at position ``x``, ``y``.
	
	.. method:: set_data(data)
	
		Replaces contents of this buffer with the string ``data``.  A ``ValueError`` exception is thrown if the string's length is not equal to  ``width * height``.
	
	.. method:: set_dot(x, y, value)
	
		Assigns the value of the dot at ``x``, ``y`` to ``value``.


.. _aux-bus-programming:

Auxiliary Bus Programming
=========================

After reset, the auxiliary bus logic waits for a command to be written to address 0 of the auxiliary bus instruction memory.  It’s therefore recommended that the programmer writes a full list of commands starting at address 1, and then follows that up with a Jump to address 1 from address 0.  Doing this ensures that the entire sequence of commands is in the memory before the auxiliary bus logic starts trying to execute them. 

Since the auxiliary bus makes use of the same data/enables bus that’s used for all of the drivers, it’s important to not let the auxiliary bus maintain ownership of the data/enables bus for extended periods of time.  It’s therefore recommended that the programmer insert a delay command of 1000 microseconds at least once in a looping auxiliary bus command sequence.

An example auxiliary bus sequence is shown below.  This list of commands results in the data values of 0-15 being written sequentially and repeatedly to the primary auxiliary bus device::

	# Initialize a list.
	commands = []

	# Make sure the command at address 0 is disabled so the program doesn’t start 
	# running before it is fully written into the instruction memory.
	commands += [pinproc.aux_command_disable()]

	# Add the commands to write out the incrementing data pattern.
	for i in range(0,16):
	  commands += [pinproc.aux_command_output_primary(i,0)]

	# Delay for 1000 microseconds.
	commands += [pinproc.aux_command_delay(1000)]

	# Jump back to address 1 to loop the program.
	commands += [pinproc.aux_command_jump(1)]

	# Send the commands to the P-ROC.
	pinproc.send_commands(0,commands)

	# Clear the commands list for a new sequence.
	commands = []

	# Jump from address 0 to address 1 to begin the program.
	commands += [pinproc.aux_command_jump(1)]

	# Send the command to the P-ROC.
	pinproc.aux_send_commands(0,commands)

	# Note - to stop the program, disable the jump at address 18
	# commands = []
	# commands += [pinproc.aux_command_disable()]
	# pinproc.aux_send_commands(18,commands)

