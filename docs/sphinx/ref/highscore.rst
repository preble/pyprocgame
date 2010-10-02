*******************
highscore Submodule
*******************

.. module:: procgame.highscore

The highscore module provides a set of classes to make gathering and displaying high score information relatively simple.   Classic Grand Champion, High Score #1-#4 style high score tables can be created with just a few lines.  With a few more lines you can gather more sophisticated high scores, such as loop champion or similar.

While :class:`InitialEntryMode` prompts the player for their initials, most developers will want to use :class:`EntrySequenceManager`, which coordinates the display of a series of :class:`InitialEntryMode` s.   :class:`EntrySequenceManager` is designed to be used with a subclass of :class:`HighScoreLogic`, which enables the developer to take advantage of these classes while using completely custom logic to determine what initials need to be prompted for.  :class:`CategoryLogic`, is a powerful :class:`HighScoreLogic` subclass that most developers will find suitable for implementing modern high score functionality.

Finally, :func:`generate_highscore_frames` can help to quickly create a traditional high score display.

Classes
=======

CategoryLogic
-------------

.. autoclass:: procgame.highscore.CategoryLogic
	:members:

HighScore
---------

.. autoclass:: procgame.highscore.HighScore
	:members:

HighScoreCategory
-----------------

.. autoclass:: procgame.highscore.HighScoreCategory
	:members:

HighScoreLogic
--------------

.. autoclass:: procgame.highscore.HighScoreLogic
	:members:

InitialEntryMode
------------------

.. autoclass:: procgame.highscore.InitialEntryMode
	:members:

EntrySequenceManager
--------------------

.. autoclass:: procgame.highscore.EntrySequenceManager
	:members:

Helper Methods
==============

.. autofunction:: procgame.highscore.generate_highscore_frames