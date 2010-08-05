************************
pinproc Module Reference
************************

.. module:: pinproc

The :mod:`pinproc` module enables control of the P-ROC hardware from within Python (using :class:`~pinproc.PinPROC`), as well as helper routines written in native code (C) to assist with tasks like DMD buffer manipulation.


PinPROC
-------

.. class:: pinproc.PinPROC(machineType)

	Represents the P-ROC hardware interface.  This class is initialized with a string, ``machineType``, which is used for the initial configuration of the P-ROC hardware interface.  Possible values include:
	
	* ``wpc``
	* ``wpc95``
	* ``wpcAlphanumeric``
	* ``sternSAM``
	* ``sternWhitestar``
	* ``custom``
	
	An ``IOError`` is raised if the P-ROC device cannot be found.  A ``ValueError`` is raised if ``machineType`` is invalid.
	
	*Note:* All I/O between the software and the P-ROC hardware is buffered to ensure maximum USB throughput.  This means that driver update commands are only sent to the hardware when the software buffer is full, or when :meth:`flush` is called.  If you are using the :class:`procgame.game.GameController` run loop you do not need to manually flush the buffers, as they are flushed after every run loop cycle.


	.. method:: aux_send_commands
	
	.. method:: dmd_draw(data)
	
		Displays the given data on the dot matrix display, which may be a :class:`DMDBuffer` (recommended) or a string (not recommended).
		
		A :class:`DMDBuffer` is interpreted as a 128x32 8-bits-per-pixel 16-color (``0x0`` thru ``0xF``) image.  Each pixel value is mapped using the mapping described in :meth:`set_dmd_color_mapping`.  A ``ValueError`` is raised if the buffer is not 128x32.
		
		If a string is passed it will be interpreted as a 128x32 image with raw 32-bits-per-pixel 8-bits-per-channel pixel data.  The channels of each pixel are summed and then divided to derive a 4-color image.
		
		If the DMD has not been previously configured using :meth:`dmd_update_config` it will be configured with the default settings prior to updating the display.
	
	.. method:: dmd_update_config(high_cycles=None)
	
		Configures the DMD using defaults except where specified otherwise.
		
		The ``high_cycles`` parameter is optional.  If supplied it must be a sequence of 4 integers representing the ``high_cycles`` values for the display.  These values affect the timing of the display (frames per second) as well as the brightness of the dots.
	

	.. method:: driver_disable(number)

		Disables (de-energizes) the specified driver number.


	.. method:: driver_pulse(number, milliseconds)
	
		
	
	.. method:: driver_schedule(number, schedule, cycle_seconds, now)
	
		
	
	.. method:: driver_patter(number, milliseconds_on, milliseconds_off, original_on_time)
	
		
	
	.. method:: driver_pulsed_patter(number, milliseconds_on, milliseconds_off, milliseconds_overall_patter_time)
	
		
	
	.. method:: driver_get_state(number)
	
		Returns a dictionary containing the state information for the specified driver.  See :ref:`driver-state-dict` for a description of the dictionary.
	
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
		
		Switch-related event types contain the switch number as the ``value``.
	
	.. method:: reset(resetFlags)
	
		Resets the P-ROC interface to its defaults.  ``resetFlags`` has two possible values:
		
		+---+------------------------------------------------------------------------------+
		| 0 | Resets the software only.                                                    |
		+---+------------------------------------------------------------------------------+
		| 1 | Resets the software to its defaults and applies the changes to the hardware. |
		+---+------------------------------------------------------------------------------+
	
	
	.. method:: set_dmd_color_mapping(mapping)
	
		Assigns the color mapping that is used by :meth:`dmd_draw`.  ``mapping`` must be a sequence of 16 integer values.  These values are initially set to 0..15, but can be modified to affect the contrast of the display and compensate for brightness differences.  Unlike :meth:`dmd_update_config` these values do not affect the timing of the display.
	
	
	.. method:: switch_get_states()
	
		Returns a list of integers representing the last known state of each switch.  See the table in :meth:`get_events` for a list of state values.
	
	
	.. method:: switch_update_rule(number, event_type, rule, linked_drivers)
	
		Configures the rule for the given switch ``number`` when its state changes to ``event_type``.
		
		``event_type`` is one of: ``'closed_debounced'``, ``'open_debounced'``, ``'closed_nondebounced'`` or ``'open_nondebounced'``.
		
		``rule`` is a dictionary with keys ``'notifyHost'`` and ``'reloadActive'``, both with integer values.
		
		``linked_drivers`` is a list of driver state dictionaries, which may be constructed with :ref:`driver-state-functions`.
	
	
	.. method:: watchdog_tickle()
	
		This method resets the hardware watchdog timer.  The timer should be tickled regularly, as the drivers are disabled when the watchdog timer expires.  The default watchdog timer period is 1 second.


.. _driver-state-functions:

Driver State Functions
----------------------

.. function:: driver_state_disable(state)

	Given a driver state dictionary (:ref:`ref <driver-state-dict>`), this function returns a modified copy of the dictionary with the driver disabled.

.. function:: driver_state_pulse(state, milliseconds)

	Given a driver state dictionary (:ref:`ref <driver-state-dict>`), this function returns a modified copy of the dictionary with the driver configured to pulse for ``milliseconds``.

.. function:: driver_state_schedule(state, schedule, seconds, now)

	Given a driver state dictionary (:ref:`ref <driver-state-dict>`), this function returns a modified copy of the dictionary with the driver configured with the given schedule parameters.

.. function:: driver_state_patter(state, milliseconds_on, milliseconds_off, original_on_time)

	Given a driver state dictionary (:ref:`ref <driver-state-dict>`), this function returns a modified copy of the dictionary with the driver configured with the given patter parameters.

.. function:: driver_state_pulsed_patter(state, milliseconds_on, milliseconds_off, milliseconds_overall_patter_time)

	Given a driver state dictionary (:ref:`ref <driver-state-dict>`), this function returns a modified copy of the dictionary with the driver configured with the given pulsed patter parameters.


.. _driver-state-dict:

Driver State Dictionary
-----------------------

+-----------------------+
| Key                   |
+=======================+
| driverNum             |
+-----------------------+
| outputDriveTime       |
+-----------------------+
| polarity              |
+-----------------------+
| state                 |
+-----------------------+
| waitForFirstTimeSlot  |
+-----------------------+
| timeslots             |
+-----------------------+
| patterOnTime          |
+-----------------------+
| patterEnable          |
+-----------------------+


.. _aux-command-functions:

Auxiliary Command Functions
---------------------------

.. function:: aux_command_output_custom(data, extra_data, enables, mux_enables)

.. function:: aux_command_output_primary(data, extra_data)




DMDBuffer
---------

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

