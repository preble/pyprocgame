# pyprocgame Overview

The P-ROC software architecture is divided into 3 layers:

- Layer 0: Serial interface to P-ROC USB.
- Layer 1: libpinproc, C API to P-ROC.
- Layer 2: High level ruleset development frameworks, such as pyprocgame.

pyprocgame is a set of Python classes designed to provide a framework for implementing mode-based custom rulesets for pinball games.  The classes make responding to abritrary and non-trivial switch events easy, as well as providing support for displaying graphics and text on the pinball display (DMD).  pyprocgame is based on pypinproc, the Python wrapper for libpinproc.

### Prerequisites

This guide is written with the assumption that you are familiar with [object-oriented programming](http://en.wikipedia.org/wiki/Object-oriented_programming) and, to a lesser extent, the [Python](http://python.org) programming language.  Terminology such as *object*, *class*, and *subclass* are used frequently within this guide and having a basic understanding of what those terms mean is important.  There is a significant amount of demo code available for pyprocgame; you should not hesitate to examine it or post to the appropriate forums if you have questions.


## What's In pyprocgame

pyprocgame provides a powerful set of classes to help you implement your game.  The following are the base classes which are used in every game:

- **GameController** -- The main game object, tieing all of the objects together: modes, coils, lamps, switches, players, configuration, and the P-ROC hardware interface itself (pypinproc).  It also manages the run loop, which polls for switch and sends DMD updates.
- **Mode** --The Mode class is subclassed by you in order to implement the various modes of your game.  By defining method names that match a certain naming convention your mode can automatically respond to switch events that the game detects.
- **ModeQueue** -- Modes are organized in the ModeQueue which is essentially a priority queue.  The ModeQueue handles notifying the active modes of switch events.  Higher priority modes receive switch events first and have the option of stopping the event from being propagated to lower priority modes.
- **Player** -- Represents a player in the game with a score.
- **Switch** -- Abstraction of a hardware switch in the game, with active and inactive state.
- **Driver** -- Abstraction of a hardware driver, such as a lamp, coil/solenoid, or flasher.

In addition, pyprocgame provides a number of classes to make controlling the dot matrix display (DMD) of your game much easier:

- **DisplayController** -- Manages the DMD by assembling the currently displayed frame from the active modes on the mode queue.
- **ScoreDisplay** -- Makes providing a classic 4-player score display extremely easy.  ScoreDisplay is implemented as a Mode that generates a DMD Frame on demand (usually to DisplayController).
- **Frame** -- A single DMD bitmap, usually 128x32.
- **Animation** -- A collection of DMD frames.
- **Font** -- A bitmap font for use with the DMD.
- **Layer** -- An abstract class; provides a sequence of DMD Frames.
- **GroupedLayer**, **ScriptedLayer**, **AnimatedLayer**, **FrameLayer**, **TextLayer** -- Implementations of the Layer class that provide the building blocks necessary to build sophisticated displays.

These classes will be described in greater depth in the sections that follow.


## What's in a pyprocgame Game?

Fortunately you won't need to understand all of those classes in order to build a pinball game with pyprocgame, but you will need is a basic understanding of how the GameController and ModeQueue work.

Let's look at a ridiculously simple game implemented with pyprocgame:

	import procgame
	game = procgame.game.GameController(machineType='wpc')
	game.load_config('mygame.yaml')
	game.enable_flippers(enable=True)
	game.run_loop()

This particular game isn't much fun, but it's a good way to demonstrate what a pyprocgame program looks like from the very highest level.  Let's see what's happening line-by-line:

	import procgame

Our first step is to import the pyprocgame module (called "procgame" in the context of Python).  This particular program assumes that pyprocgame is in your sys.path.  If it's not, you will need to modify sys.path.

	game = procgame.game.GameController(machineType='wpc')

Next we create a new GameController object.  This is the central object in your pinball game.  It maintains collections for all of the switches, lamps and coils, as well as players in the current game.  It also contains a ModeQueue, which we'll cover later.  *If this were an actual full-blown pyprocgame program we would create our own subclass of GameController.*

Note that the connection to the P-ROC hardware is established in the constructor for GameController and the hardware is reset to obtain a known state.  We pass the machineType value as 'wpc' in order to initialize P-ROC to the proper settings for controlling a WPC driver board.

	game.load_config('mygame.yaml')

Here we load a [YAML](http://yaml.org/) file that describes the pinball hardware.  The P-ROC software uses YAML files (a "human-friendly data serialization standard") to describe the machine that the P-ROC hardware is connected to.  This statement loads the configuration and configures all of the switches, lamps and coils, as well as the flippers so that we can...

	game.enable_flippers(enable=True)

It wouldn't be pinball without flippers; here's where we turn them on.  The pyprocgame code behind this statement uses the machine description (from the YAML file previously loaded with load\_config()) to create the association between the flipper buttons (switches) and the flipper coils.

Internally, this takes advantage of P-ROC's switch rules feature, which enables a hardware-triggered linkage between switch events and coil drivers to guarantee that when the player hits the flipper button the coil will be fired immediately.  This keeps P-ROC-based games responsive, rather than suffering from any latency between the computer host processing of the switch event and activating the coil driver.  The same principle can be applied to pop bumpers.

	game.run_loop()

Finally we start the game's run loop, which allows the game to actually run.  The run loop checks for events from the P-ROC hardware and sends them to the ModeQueue so that they can be responded to by your game code.  This method call is blocking and does not return until program execution is interrupted (usually by a Ctrl-C).


## Onward to Deeper Rulesets

Most pinball games are a bit more sophisticated than just hitting the flippers.  You usually have targets to hit, banks of drop targets to knock down, and so on.  In the abstract those features seem pretty easy to implement: respond to the switch event and award points.  But what about more complex rulesets?  Multiball?  *Stacked* multiballs?  Things can get complicated quickly!

When we were designing pyprocgame our goal was to enable the developer (that's you) to create rulesets that are as complicated as they can imagine while keeping the task of implementing (and debugging) those rulesets as sane as possible.  Just like you, we want to design our own games, and we want to have fun doing it.  

To reiterate the above, we designed pyprocgame to be flexible enough to allow you to create any game ruleset you can imagine, yet provide enough of a framework to help you get off the ground quickly.  We've strived to keep the features modular and limit interdependence so that if, for example, you want to write your own routines to control the DMD you can do so, or if you want to create your own mode system you can replace ours and still take advantage of the Python interface to libpinproc and the DMD utilities.

## Modes and the ModeQueue

We've been talking about pyprocgame at a very high level, but let's get down to specifics for a moment:

Mode objects are the building blocks of pyprocgame games.  In pyrpocgame a mode is *a functional subset of a game that receives switch events*.   When active, modes are organized in a queue (ModeQueue), which determines the order in which they receive switch events.  That is, when the GameController's run\_loop() receives a switch event from the P-ROC hardware, only objects in the ModeQueue will be notified of the event.  If you want your game to react to a switch event, one or more of your modes must be given that responsibility.

We subclass Mode to create our own useful modes.  Let's look at a simple mode:

	class FirstMode(procgame.game.Mode):
		def __init__(self, game):
			super(FirstMode, self).__init__(game=game, priority=5)
		
		def sw_startButton_active(self, sw):
			print("Start!")
			return True

Here we have defined a class, FirstMode, which subclasses the procgame Mode class.  The Mode constructor takes 2 parameters.  *Game* is a reference to an instance of our own GameController subclass, and *priority* governs the order in which this mode will receive events, relative to the others – more on that later.

Next we define a method with a rather distinctive name: *sw\_startButton\_active()*.  This is our switch event handler.  When a Mode is instantiated its method list is scanned for methods that match a certain naming pattern: *sw\_(switch name)_active* in this case.  This tells pyprocgame that it should call this method when the button named startButton is active (closed in this case; this is configurable for each switch using the YAML file).  

Similarly, a method named *sw\_trainWreck\_inactive()* would be called when the trainWreck switch had changed to an inactive state.  The switch name in these method names must correspond to a switch name in the YAML configuration; otherwise a warning message will be printed when instantiating the class.  More on switch even handlers (including responding to events after a delay) later.

Our switch handler in this case is very simple.  It prints out a message and returns True.  Each switch event handler must return True or False.  A return value of True tells the ModeQueue to allow this switch event to be sent to other active modes; a return value of False instructs ModeQueue to stop processing this event.

This is where the priority of a mode becomes important.  The ModeQueue is essentially a priority queue: the highest-priority modes receive switch events first.  If they do not return False, the switch event is then sent to lower priority modes.  In this way you can use a high priority mode to give switches on the playfield to have special meaning during any number of modes, without having to handle that special case alongside the code for the more normal meaning of the switch.  Or you can easily have a switch result in multiple mode triggers.


### Mode Management

Now that we have a mode, how do we add it to the ModeQueue so that it will receive events?  Let's create a more mature example game by subclassing GameController, assuming our FirstMode class is defined elsewhere in the file:

	class ExampleGame(procgame.game.GameController):
		def __init__(self, machineType):
			super(ExampleGame, self).__init__(machineType)
			self.load_config('mygame.yaml')
			
		def reset(self):
			super(ExampleGame, self).reset()
			first_mode = FirstMode(self)
			self.modes.add(first_mode)
			self.enable_flippers(enable=True)
			
	game = ExampleGame(machineType='wpc')
	game.reset()
	game.run_loop()

We've reorganized the code a bit to reflect the recommended layout for pyprocgame games.  First we moved the configuration loading to the constructor, and added an override for GameController#reset(), which is called to reset the state of the game and the hardware.  Because the ModeQueue (self.modes in this context -- every GameController has a ModeQueue at self.modes) is cleared by reset(), we can simply add an instance of our mode at this point.

### Other Mode Features

In some cases you may wish to respond to a switch event only after the switch has been in that state for a certain time period.  The Mode class provides a means for accomplishing this with incredible ease -- just add a _for\_(time period)_ suffix to the normal switch method convention:

- sw\_switchName\_active\_for\_500ms() -- called once switchName is active for 500 milliseconds
- sw\_switchName\_inactive\_for\_3s() -- called once switchName is inactive for 3 seconds
- sw\_switchName\_inactive\_for\_20ms() -- called once switchName is inactive for 20 milliseconds

You can also schedule a method to be called after a specified delay using Mode#delay():

	def sw_target1_active(self, sw):
		self.delay(name='example), event_type=None, 
		           delay=0.5, handler=self.delayed_event)
		return True
	
	def delayed_target(self):
		print("It's been 500 milliseconds!")

Mode subclasses can also implement the following methods to receive and respond to changes in state:

- mode\_started() -- Called when the mode is added to the ModeQueue.
- mode\_stopped() -- Called when the mode is removed from the ModeQueue.
- mode\_topmost() -- Called when the mode is the mode with the highest priority on the ModeQueue, and therefore the first to receive all switch events.
- mode\_tick() -- Called each time the run\_loop() completes one 'cycle' of reading events and processing them.  This method will be called many, many times per second on every mode in the mode queue and so should be brief in order to keep the run loop running quickly.


### Thoughts on Planning and Design of Modes

Modes can be very course-grained, such as a mode that controls all of multiball from start to finish (Multiball), or very fine-grained (MultiballActivate, MultiballRunning, MultiballJackpot, MultiballRestart).  It's up to you to determine how you want to lay out your modes.

Additionally, it's important to note that modes do not need to correspond to modes on your playfield.  You can create a Mode subclass and add it to the ModeQueue and use it for all sorts of things within your game: displays, timers, visual effects, service mode, initial entry, and so on.


## Drivers

We've spent a good amount of time talking about how to react to events within the game, but a huge part of pinball is affecting changes within the game: powering coils, turning lamps on and off, and pulsing flashers.  Once you have a fleshed out YAML file for your machine, you can easily control individual elements of the game by accessing them within the GameController subclass.  Since you'll usually be making these changes from within switch handlers, we'll show the examples in that context:

	def sw_someButton_active(self, sw):
		self.game.lamps.startButton.schedule(schedule=0xff00ff00, 
			cycle_seconds=0, now=True)
	
		self.game.coils.popper.pulse(50)
	
		self.game.lamps.shootAgain.pulse(0) # Turn on indefinitely.


## YAML Configuration File

*To be written.*


## Dot Matrix Display

*To be written.*


## Stock Modes

*To be written, a discussion on the various "stock modes" which may be incorporated into your game to add functionality.*

