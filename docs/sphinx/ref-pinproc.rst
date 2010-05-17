pinproc Module Reference
------------------------

DMDBuffer
=========

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
