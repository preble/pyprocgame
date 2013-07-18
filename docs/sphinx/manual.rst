*****************
pyprocgame Manual
*****************

The P-ROC software architecture is divided into 3 layers:

* Layer 0: Serial interface to P-ROC USB.
* Layer 1: libpinproc, C API to P-ROC.
* Layer 2: High level ruleset development frameworks, such as pyprocgame.

pyprocgame is a set of Python classes designed to provide a framework for implementing mode-based custom rulesets for pinball games.  The classes make responding to abritrary and non-trivial switch events easy, as well as providing support for displaying graphics and text on the pinball display (DMD).  pyprocgame is based on pypinproc, the Python wrapper for libpinproc.

Prerequisites
=============

This guide is written with the assumption that you are familiar with `object-oriented programming <http://en.wikipedia.org/wiki/Object-oriented_programming>`_ and, to a lesser extent, the `Python <http://python.org>`_ programming language.  Terminology such as *object*, *class*, and *subclass* are used frequently within this guide and having a basic understanding of what those terms mean is important.  There is a significant amount of demo code available for pyprocgame; you should not hesitate to examine it or post to the appropriate forums if you have questions.


What's In pyprocgame
====================

pyprocgame provides a powerful set of classes to help you implement your game.  The following are the base classes which are used in every game:

- :class:`~procgame.game.GameController` -- The main game object, tying all of the objects together: modes, coils, lamps, switches, players, configuration, and the P-ROC hardware interface itself (pypinproc).  It also manages the run loop, which polls for switch and sends DMD updates.
- :class:`~procgame.game.Mode` -- The Mode class is subclassed by you in order to implement the various modes of your game.  By defining method names that match a certain naming convention your mode can automatically respond to switch events that the game detects.
- :class:`~procgame.game.ModeQueue` -- Modes are organized in the ModeQueue which is essentially a priority queue.  The ModeQueue handles notifying the active modes of switch events.  Higher priority modes receive switch events first and have the option of stopping the event from being propagated to lower priority modes.
- :class:`~procgame.game.Player` -- Represents a player in the game with a score.
- :class:`~procgame.game.Switch` -- Abstraction of a hardware switch in the game, with active and inactive state.
- :class:`~procgame.game.Driver` -- Abstraction of a hardware driver, such as a lamp, coil/solenoid, or flasher.

In addition, pyprocgame provides a number of classes to make controlling the dot matrix display (DMD) of your game much easier:

- :class:`~procgame.dmd.DisplayController` -- Manages the DMD by assembling the currently displayed frame from the active modes on the mode queue.
- :class:`~procgame.modes.ScoreDisplay` -- Makes providing a classic 4-player score display extremely easy.  ScoreDisplay is implemented as a Mode that generates a DMD Frame on demand (usually to DisplayController).
- :class:`~procgame.dmd.Frame` -- A single DMD bitmap, usually 128x32.
- :class:`~procgame.dmd.Animation` -- A collection of DMD frames.
- :class:`~procgame.dmd.Font` -- A bitmap font for use with the DMD.
- :class:`~procgame.dmd.Layer` -- An abstract class; provides a sequence of DMD Frames.
- :class:`~procgame.dmd.GroupedLayer`, :class:`~procgame.dmd.ScriptedLayer`, :class:`~procgame.dmd.AnimatedLayer`, :class:`~procgame.dmd.FrameLayer`, :class:`~procgame.dmd.TextLayer` -- Implementations of the Layer class that provide the building blocks necessary to build sophisticated displays.

These classes will be described in greater depth in the sections that follow.


What's in a pyprocgame Game?
============================

Fortunately you won't need to understand all of those classes in order to build a pinball game with pyprocgame, but you will need is a basic understanding of how the :class:`~procgame.game.GameController` and :class:`~procgame.game.ModeQueue` work.

Let's look at a ridiculously simple game implemented with pyprocgame::

	import pinproc
	import procgame.game
	game = procgame.game.GameController(machine_type=pinproc.MachineTypeWPC)
	game.load_config('mygame.yaml')
	game.enable_flippers(enable=True)
	game.run_loop()

This particular game isn't particularly deep, but it's a good way to demonstrate what a pyprocgame program looks like from the very highest level.  Let's see what's happening line-by-line::

    import pinproc

Our first step is to import the pinproc module, which contains some useful constants. It also contains a lower-level interface to the P-ROC, which pyprocgame relies upon.

	import procgame.game

Next we'll import the procgame.game module, which contains higher level classes used by most games.  This particular program assumes that pyprocgame is in your sys.path.  If it's not, you will need to modify sys.path. ::

	game = procgame.game.GameController(machine_type=pinproc.MachineTypeWPC)

Next we create a new :class:`~procgame.game.GameController` object.  This is the central object in your pinball game.  It maintains collections for all of the switches, lamps and coils, as well as players in the current game.  It also contains a :class:`~procgame.game.ModeQueue`, which we'll cover later.  (If this were an actual full-blown pyprocgame program we would create our own subclass of :class:`~procgame.game.GameController`.)

Note that the connection to the P-ROC hardware is established in the constructor for :class:`~procgame.game.GameController` and the hardware is reset to obtain a known state.  We pass the ``machine_type`` value as ``'wpc'`` in order to initialize P-ROC to the proper settings for controlling a WPC driver board. ::

	game.load_config('mygame.yaml')

Here we load a YAML file that describes the pinball hardware.  The P-ROC software uses YAML files (a "human-friendly data serialization standard") to describe the machine that the P-ROC hardware is connected to (see :ref:`machine-config` for a complete description of these files).  This statement loads the configuration and configures all of the switches, lamps and coils, as well as the flippers so that we can... ::

	game.enable_flippers(enable=True)

It wouldn't be pinball without flippers; here's where we turn them on.  The pyprocgame code behind this statement uses the machine description (from the YAML file previously loaded with :meth:`~procgame.game.GameController.load_config`) to create the association between the flipper buttons (switches) and the flipper coils.

Internally, this takes advantage of P-ROC's switch rules feature, which enables a hardware-triggered linkage between switch events and coil drivers to guarantee that when the player hits the flipper button the coil will be fired immediately.  This keeps P-ROC-based games responsive, rather than suffering from any latency between the computer host processing of the switch event and activating the coil driver.  The same principle can be applied to pop bumpers. ::

	game.run_loop()

Finally we start the game's run loop, which allows the game to actually run.  The run loop checks for events from the P-ROC hardware and sends them to the :class:`~procgame.game.ModeQueue` so that they can be responded to by your game code.  This method call is blocking and does not return until program execution is interrupted (usually by a Ctrl-C).


Onward to Deeper Rulesets
=========================

Most pinball games are a bit more sophisticated than just hitting the flippers.  You usually have targets to hit, banks of drop targets to knock down, and so on.  In the abstract those features seem pretty easy to implement: respond to the switch event and award points.  But what about more complex rulesets?  Multiball?  *Stacked* multiballs?  Things can get complicated quickly!

When we were designing pyprocgame our goal was to enable the developer (that's you) to create rulesets that are as complicated as they can imagine while keeping the task of implementing (and debugging) those rulesets as sane as possible.  Just like you, we want to design our own games, and we want to have fun doing it.  

To reiterate the above, we designed pyprocgame to be flexible enough to allow you to create any game ruleset you can imagine, yet provide enough of a framework to help you get off the ground quickly.  We've strived to keep the features modular and limit interdependence so that if, for example, you want to write your own routines to control the DMD you can do so, or if you want to create your own mode system you can replace ours and still take advantage of the Python interface to libpinproc and the DMD utilities.


Modes and the ModeQueue
=======================

We've been talking about pyprocgame at a very high level, but let's get down to specifics for a moment:

Mode objects are the building blocks of pyprocgame games.  In pyrpocgame a mode is *a functional subset of a game that receives switch events*.   When active, modes are organized in a queue (:class:`~procgame.game.ModeQueue`), which determines the order in which they receive switch events.  That is, when the :class:`~procgame.game.GameController`'s :meth:`~procgame.game.GameController.run_loop` receives a switch event from the P-ROC hardware, only objects in the :class:`~procgame.game.ModeQueue` will be notified of the event.  If you want your game to react to a switch event, one or more of your modes must be given that responsibility.

We subclass :class:`~procgame.game.Mode` to create our own useful modes.  Let's look at a simple mode::

	class FirstMode(procgame.game.Mode):
	  def __init__(self, game):
	    super(FirstMode, self).__init__(game=game, priority=5)
	
	  def sw_startButton_active(self, sw):
	    print("Start!")
	    return procgame.game.SwitchStop

Here we have defined a class, :class:`FirstMode`, which subclasses the procgame :class:`~procgame.game.Mode` class.  The :class:`~procgame.game.Mode` constructor takes 2 parameters.  ``game`` is a reference to an instance of our own :class:`~procgame.game.GameController` subclass, and ``priority`` governs the order in which this mode will receive events, relative to the others – more on that later.

Next we define a method with a rather distinctive name: ``sw_startButton_active()``.  This is our switch event handler.  When a :class:`~procgame.game.Mode` is instantiated its method list is scanned for methods that match a certain naming pattern: ``sw_(switch name)_active`` in this case.  This tells pyprocgame that it should call this method when the button named ``startButton`` is active (closed in this case; this is configurable for each switch using the YAML file).  

Similarly, a method named ``sw_trainWreck_inactive()`` would be called when the trainWreck switch had changed to an inactive state.  The switch name in these method names must correspond to a switch name in the YAML configuration; otherwise a warning message will be printed when instantiating the class.  More on switch even handlers (including responding to events after a delay) later.

Our switch handler in this case is very simple.  It prints out a message and returns :data:`procgame.game.SwitchStop`.  Each switch event handler must return :data:`~procgame.game.SwitchStop` or :data:`~procgame.game.SwitchContinue`.  A return value of stop instructs :class:`~procgame.game.ModeQueue` to stop processing this event; a return value of continue tells the :class:`~procgame.game.ModeQueue` to allow this switch event to be sent to other active modes.  If you do not explicitly return a value from a switch handler method the behavior will be the same as if :data:`~procgame.game.SwitchContinue` had been returned.

.. note::
	Previously switch handlers returned ``True`` or ``False`` to indicate :data:`~procgame.game.SwitchStop` or :data:`~procgame.game.SwitchContinue`, respectively.  This practice has been superseded by these constants for clarity.  They are backward compatible.

This is where the priority of a mode becomes important.  The :class:`~procgame.game.ModeQueue` is essentially a priority queue: the highest-priority modes receive switch events first.  If the switch handler returns continue the switch event is then sent to lower priority modes.  In this way you can use a high priority mode to give switches on the playfield to have special meaning during any number of modes, without having to handle that special case alongside the code for the more normal meaning of the switch.  Or you can easily have a switch result in multiple mode triggers.


Mode Management
---------------

Now that we have a mode, how do we add it to the :class:`~procgame.game.ModeQueue` so that it will receive events?  Let's create a more mature example game by subclassing :class:`~procgame.game.GameController`, assuming our :class:`FirstMode` class is defined elsewhere in the file::

	class ExampleGame(procgame.game.GameController):
	  def __init__(self, machine_type):
	    super(ExampleGame, self).__init__(machine_type)
	    self.load_config('mygame.yaml')
	
	  def reset(self):
	    super(ExampleGame, self).reset()
	    first_mode = FirstMode(self)
	    self.modes.add(first_mode)
	    self.enable_flippers(enable=True)
	
	game = ExampleGame(machine_type='wpc')
	game.reset()
	game.run_loop()

We've reorganized the code a bit to reflect the recommended layout for pyprocgame games.  First we moved the configuration loading to the constructor, and added an override for :meth:`procgame.game.GameController.reset`, which is called to reset the state of the game and the hardware.  Because the :class:`~procgame.game.ModeQueue` (self.modes in this context -- every :class:`~procgame.game.GameController` has a :class:`~procgame.game.ModeQueue` at self.modes) is cleared by :meth:`reset`, we can simply add an instance of our mode at this point.

Other Mode Features
-------------------

Timed Switch Handlers
`````````````````````

In some cases you may wish to respond to a switch event only after the switch has been in that state for a certain time period.  The Mode class provides a means for accomplishing this with incredible ease -- just add a ``_for_(time period)_`` suffix to the normal switch method convention:

- ``sw_switchName_active_for_500ms()`` -- called once switchName is active for 500 milliseconds
- ``sw_switchName_inactive_for_3s()`` -- called once switchName is inactive for 3 seconds
- ``sw_switchName_inactive_for_20ms()`` -- called once switchName is inactive for 20 milliseconds


Scheduling Delayed Method Calls
```````````````````````````````

You can schedule a method to be called after a specified delay using :meth:`procgame.game.Mode.delay`::

	def sw_target1_active(self, sw):
	  self.delay(delay=0.5, handler=self.delayed_event)
	  return True
	
	def delayed_target(self):
	  print("It's been 500 milliseconds!")

If you want to cancel a delay at a later time, store the return value from :meth:`delay`::

    def sw_target1_active(self, sw):
      self.delayed_name = self.delay(delay=0.5, handler=self.delayed_event)
    
    def sw_target2_active(self, sw):
      # Cancel the previously-scheduled delay:
      self.cancel_delayed(self.delayed_name)

    def delayed_target(self):
      print("It's been 500 milliseconds!")


Mode Status Methods
```````````````````

Mode subclasses can also implement the following methods to receive and respond to changes in state:

- :meth:`~procgame.game.Mode.mode_started` -- Called when the mode is added to the ModeQueue.
- :meth:`~procgame.game.Mode.mode_stopped` -- Called when the mode is removed from the ModeQueue.
- :meth:`~procgame.game.Mode.mode_topmost` -- Called when the mode is the mode with the highest priority on the ModeQueue, and therefore the first to receive all switch events.
- :meth:`~procgame.game.Mode.mode_tick` -- Called each time the run_loop() completes one 'cycle' of reading events and processing them.  This method will be called many, many times per second on every mode in the mode queue and so should be brief in order to keep the run loop running quickly.


Thoughts on Planning and Design of Modes
----------------------------------------

Modes can be very course-grained, such as a mode that controls all of multiball from start to finish (Multiball), or very fine-grained (MultiballActivate, MultiballRunning, MultiballJackpot, MultiballRestart).  It's up to you to determine how you want to lay out your modes.

Additionally, it's important to note that modes do not need to correspond to modes on your playfield.  You can create a Mode subclass and add it to the :class:`~procgame.game.ModeQueue` and use it for all sorts of things within your game: displays, timers, visual effects, service mode, initial entry, and so on.


Drivers
=======

We've spent a good amount of time talking about how to react to events within the game, but a huge part of pinball is affecting changes within the game: powering coils, turning lamps on and off, and pulsing flashers.  Once you have a fleshed out YAML file for your machine, you can easily control individual elements of the game by accessing them within the GameController subclass.  Since you'll usually be making these changes from within switch handlers, we'll show the examples in that context::

	def sw_someButton_active(self, sw):
	  self.game.lamps.startButton.schedule(schedule=0xff00ff00, 
	    cycle_seconds=0, now=True)
	
	  self.game.coils.popper.pulse(50)
	
	  self.game.lamps.shootAgain.pulse(0) # Turn on indefinitely.


Configuration Files
===================

pyprocgame uses configuration files in the `YAML <http://yaml.org/>`_ format.  YAML is a human-readable structured text file format.  Configuration files generally consist of a set of "keys" at the top level

.. _machine-config:

Machine Configuration Files
---------------------------

Machine configuration files describe the physical components of a pinball machine: coils, lamps, switches, etc., and make it easier to refer to those components in code.  The following is a subset a machine configuration file for Judge Dredd (JD.yaml)::

	PRGame:
	  machineType: wpc
	  numBalls: 6
	PRFlippers:
	  - flipperLwR
	  - flipperLwL
	PRBumpers:
	  - slingL
	PRSwitches:
	  flipperLwR:
	    number: SF2
	  flipperLwL: 
	    number: SF4
	  leftRampToLock:
	    number: S63
	    type: 'NC'
	PRCoils:
	  flipperLwRMain: 
	    number: FLRM
	PRLamps:
	  perp1W:
	    number: L11
	  perp1R:
	    number: L12



.. _system-config:

System Configuration Files
--------------------------

System configuration files contain values common to all games, and values specific to the system being developed on, such as file paths.  The configuration file is managed by the :mod:`procgame.config` module; you can retrieve values from the configuration using :func:`~procgame.config.value_for_key_path`.

The configuration file is located at ``~/.pyprocgame/config.yaml``.  Note that the tilde (~) is a UNIX convention meaning the user's home directory.

.. note::

	Windows Users

	On Windows it can be tricky to determine your home directory.  Luckily pyprocgame prints out the full path that it expects to find the config.yaml file at.  Make sure that the path that pyprocgame prints matches where you placed your configuration file.

	If you encounter difficulty creating a ``.pyprocgame`` directory in Windows, try using the command print: ``mkdir .pyprocgame``.  Yes, that's "dot-pyprocgame".  Dot-files and dot-folders are common in UNIX-like systems.  By default they are not shown in directory listings.

	When creating your config.yaml file, be sure that its actual extension is ``.yaml``, not ``.txt``.  Some components of Windows like to add a ``.txt`` extension when you are not expecting it.


An example config.yaml file follows::

	font_path:
	 - ~/Projects/PROC/shared/dmd
	 - ~/Projects/PROC/my_fonts
	config_path:
	 - ~/Projects/PROC/shared/config

``font_path`` is used by :func:`~procgame.dmd.font_named`, while ``config_path`` is used by :func:`~procgame.game.config_named`.


Dot Matrix Display (DMD) Control
================================

pyprocgame Display Architecture
-------------------------------

There are a lot of different ways one could run a DMD with pyprocgame, but here we're going to talk about the recommended approach, which is well-integrated with the mode queue system.  Let's talk about how the P-ROC hardware works first.  The P-ROC board provides a three hardware frame buffers, displaying them in order as new frames are provided by the software.  This helps keep the display smooth to avoid hiccups caused by operating system scheduling variances.  Much like a switch event, P-ROC sends a DMD event when it's ready to display another frame.  So if we send the next frame whenever we see this event, we can keep P-ROC's frame buffers full and maintain smooth, skipless video.

The :class:`~procgame.dmd.DisplayController` class makes this pretty easy.  Here's how we incorporate it into our :class:`GameController` subclass::

	class DemoGame(game.GameController):
	  def __init__(self, machine_type):
	    super(DemoGame, self).__init__(machine_type)
	    self.dmd = dmd.DisplayController(self, 128, 32)
	
	  def dmd_event(self):
	    self.dmd.update()        

That's great, but how do we tell the :class:`DisplayController` what to display?  Every time :meth:`DisplayController.update() <procgame.dmd.DisplayController.update>` is called it traverses the mode queue and asks each mode if it has a DMD frame to display.  If it does, it composites it upon the frames of lower priority modes.  Once it has the final frame assembled it is uploaded to the P-ROC hardware.  

Note the order in which the frames are composited: *frames from lower priority modes are overwritten by higher priority frames*.  So imagine that you have laid out your modes like this:

  * Priority 1 (low): General game play mode.  Provides a frame showing the score.
  * Priority 5 (medium): "Hurry-up" mode.  Provides a frame showing the hurry-up countdown and jackpot value.

If you've been thinking about how you'd organize your modes already, this is the sort of pattern that you should follow for switch events.  More specialized modes get first crack at the switch events due to their priority.  This pattern also works well with :class:`DisplayController`: the hurry-up information is shown to the player when that mode is active; otherwise the score is shown.

How does the mode supply the DMD frame to :class:`DisplayController`, though?  To explain that we first need to introduce the Layer class, which provides a sequence of frames via its method :meth:`~procgame.dmd.Layer.next_frame`.  There are a number of useful :class:`~procgame.dmd.Layer` subclasses provided with pyprocgame:

  * :class:`~procgame.dmd.FrameLayer`: Provides an endless sequence of one frame (dmd.Frame).
  * :class:`~procgame.dmd.AnimatedLayer`: Provides an ordered sequence of dmd.Frame objects.
  * :class:`~procgame.dmd.TextLayer`: Uses a dmd.Font to display a text string to the user.
  * :class:`~procgame.dmd.GroupedLayer`: Composites the output of multiple Layer subclasses into one common output.  This can be used to create complicated displays with numerous subcomponents.
  * :class:`~procgame.dmd.ScriptedLayer`: Runs a simple "script" (dictionary) to display a sequence of layers, showing each layer for a specified amount of time.

:class:`DisplayController` checks for an attribute on each :class:`Mode` class called :attr:`layer`.  If the mode has a layer, the :meth:`next_frame` from that layer is used; otherwise it is ignored.  Let's add a layer to an example mode::

	class HurryUpMode(game.Mode):
	  def __init__(self):
	    super(HurryUpMode, self).__init__(priority=5)
	    self.layer = dmd.TextLayer(x=128/2, y=8, font=my_font, justify="center")
	  def update_countdown_display(self, seconds):
	    self.layer.set_text('%d seconds' % (seconds));


Animations, Frames, and Fonts
-----------------------------

*To be written.*


