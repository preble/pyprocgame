*************
dmd Submodule
*************

.. module:: procgame.dmd

The dmd submodule provides classes and functions to facilitate generating both text and graphics for on the dot matrix display:

* Load and save :file:`.dmd` files from/to disk using :meth:`Animation.load` and :meth:`~Animation.save`.
* Extract and reorder individual :class:`Frame` objects that compose an :class:`Animation` with :attr:`Animation.frames`.
* Use :class:`Layer` subclasses such as :class:`GroupedLayer` to control and generate sophisticated sequences.
* Display a sequence of frames using :class:`AnimatedLayer`.
* Automatically update the DMD based on the active modes using :class:`DisplayController`.

Overview
========

The pyprocgame display system is designed specifically to take advantage of the mode queue architecture.  This provides the game developer with a relatively simple means to supply the player with the most relevant information at all times.

The :class:`DisplayController` class is the glue that makes this architecture work.  If you wish to implement a different architecture you can certainly ignore :class:`DisplayController` but most developers will want to take advantage of it.

When integrated within your :class:`~procgame.game.GameController` subclass, :class:`DisplayController`'s :meth:`~DisplayController.update` method is called whenever the DMD is ready for a new frame.  :meth:`update` iterates over the mode queue in search of modes that have a :attr:`layer` attribute.  This attribute should be an instance of a subclass of :class:`Layer`, which provides a sequence of frames, one at a time, via its :meth:`~Layer.next_frame` method.  If a mode does not provide this layer attribute it is ignored; otherwise the next frame is obtained and the frames are composited from bottom to top (lowest priority modes being at the bottom).

All layers have an :attr:`Layer.opaque` attribute, which defaults to ``False``.  If a layer is opaque, no layers below that one (with lower priority) will be fetched or composited.  Also, if a layer's :meth:`next_frame` method returns ``None`` it is considered to be transparent.

By using this mode-layer arrangement the developer has a direct connection between modes and what's being displayed, without having to manage a separate display queue.  For example, the score display might be a layer associated with a low-priority mode.  If the game enters a hurry-up mode, which has a higher priority due to its interest in switch events, the hurry-up mode can supply its own layer which is automatically displayed above the score layer.

..
	TODO: Talk about transitions and their hook-in in layers.


Core Classes
============

Animation
---------
.. autoclass:: procgame.dmd.Animation
	:members:

DisplayController
-----------------
.. autoclass:: procgame.dmd.DisplayController
    :members:

Font
-----
.. autoclass:: procgame.dmd.Font
	:members:

Frame
-----
.. autoclass:: procgame.dmd.Frame
	:members:

Layer
-----
.. autoclass:: procgame.dmd.Layer
    :members:



Layer Subclasses
================

Subclasses of :class:`Layer` that provide building blocks for sophisticated display effects.

AnimatedLayer
-------------
.. autoclass:: procgame.dmd.AnimatedLayer
    :members:

FrameLayer
----------
.. autoclass:: procgame.dmd.FrameLayer
    :members:

GroupedLayer
------------
.. autoclass:: procgame.dmd.GroupedLayer
    :members:


ScriptedLayer
-------------
.. autoclass:: procgame.dmd.ScriptedLayer
    :members:

TextLayer
---------
.. autoclass:: procgame.dmd.TextLayer
    :members:


.. 
	Undocumented for now:

	Layer Transitions
	=================

	LayerTransitionBase
	-------------------
	.. autoclass:: procgame.dmd.LayerTransitionBase
		:members:

	CrossFadeTransition
	-------------------
	.. autoclass:: procgame.dmd.CrossFadeTransition
		:members:

	ExpandTransition
	----------------
	.. autoclass:: procgame.dmd.ExpandTransition
		:members:

	PushLayerTransition
	-------------------
	.. autoclass:: procgame.dmd.PushLayerTransition
		:members:

	SlideOverLayerTransition
	------------------------
	.. autoclass:: procgame.dmd.SlideOverLayerTransition
		:members:



Utilities
=========

Font Utilities
--------------

.. autofunction:: procgame.dmd.font_named
.. autodata:: procgame.dmd.font_path

MarkupFrameGenerator
--------------------

.. autoclass:: procgame.dmd.MarkupFrameGenerator
	:members:

.. 
	Undocumented for now:

	TransitionOutHelperMode
	-----------------------

	.. autoclass:: procgame.dmd.TransitionOutHelperMode
		:members:

