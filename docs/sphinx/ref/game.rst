**************
game Submodule
**************

.. module:: procgame.game

The :mod:`procgame.game` submodule contains the core building blocks of a pyprocgame-based game.
See :doc:`/manual` for a discussion on how to create a pyprocgame game.

Core Classes
============

AttrCollection
--------------
.. autoclass:: procgame.game.AttrCollection
	:members:

Driver
------
.. autoclass:: procgame.game.Driver
	:members:

GameController
--------------
.. autoclass:: procgame.game.GameController
    :members:

GameItem
--------
.. autoclass:: procgame.game.GameItem
	:members:

Mode
----
.. autoclass:: procgame.game.Mode
    :members:

ModeQueue
---------
.. autoclass:: procgame.game.ModeQueue
    :members:

Player
------
.. autoclass:: procgame.game.Player
	:members:

Switch
------
.. autoclass:: procgame.game.Switch
	:members:

Helper Classes
==============

BasicGame
---------
.. autoclass:: procgame.game.BasicGame
	:members:


Constants
=========

.. data:: procgame.game.SwitchContinue

	Used as a return value from a :class:`~procgame.game.Mode` switch handler to indicate that lower priority modes should receive this switch event.

.. data:: procgame.game.SwitchStop

	Used as a return value from a :class:`~procgame.game.Mode` switch handler to indicate that lower priority modes should not receive this switch event.
