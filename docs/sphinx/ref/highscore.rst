*******************
highscore Submodule
*******************

.. module:: procgame.highscore

Overview
========

The highscore module provides a set of classes to make gathering and displaying high score information relatively simple.   Classic Grand Champion, High Score #1-#4 style high score tables can be created with just a few lines.  With a few more lines you can gather more sophisticated high scores, such as loop champion or similar.

While :class:`InitialEntryMode` prompts the player for their initials, most developers will want to use :class:`EntrySequenceManager`, which coordinates the display of a series of :class:`InitialEntryMode` s.   :class:`EntrySequenceManager` is designed to be used with a subclass of :class:`HighScoreLogic`, which enables the developer to take advantage of these classes while using completely custom logic to determine what initials need to be prompted for.  :class:`CategoryLogic`, is a powerful :class:`HighScoreLogic` subclass that most developers will find suitable for implementing modern high score functionality.

Finally, :func:`generate_highscore_frames` can help to quickly create a traditional high score display.

Using EntrySequenceManager
--------------------------

In your :class:`GameController` subclass's setup method, configure the categories you wish to track scores for.  The categories are used each time the game ends, as we'll see in the next step.  In this case we'll setup two categories: a 'classic' category for the traditional Grand Champion and high scores 1-4, and a more modern 'loop champ' category.  We set :attr:`score_for_player` to tell the category how to obtain that particular score value.  Note that because the loop champ only has one title, only the highest loop score will be saved.  The number of titles is used to determine how many scores are saved. ::

	def setup(self):
	    self.highscore_categories = []

	    cat = highscore.HighScoreCategory()
	    cat.game_data_key = 'ClassicHighScoreData'
	    cat.titles = ['Grand Champion', 'High Score 1', ... , `High Score 4`]
	    self.highscore_categories.append(cat)

	    cat = highscore.HighScoreCategory()
	    cat.game_data_key = 'LoopsHighScoreData'
	    cat.titles = ['Loop Champ']
	    cat.score_for_player = lambda category, player: player.loops
	    cat.score_suffix_singular = ' loop'
	    cat.score_suffix_plural = ' loops'
	    self.highscore_categories.append(cat)

	    for category in self.highscore_categories:
	        category.load_from_game(self)

We use :class:`EntrySequenceManager` to manage the high score prompting process once the game has finished.  We instantiate it like a normal mode, set the finished handler and logic, and then add it to the mode queue::

	def game_ended(self):
	    seq_manager = highscore.EntrySequenceManager(game=self, priority=2)
	    seq_manager.finished_handler = self.highscore_entry_finished
	    seq_manager.logic = highscore.CategoryLogic(game=self, categories=self.highscore_categories)
	    self.modes.add(seq_manager)

Finally, we write the finished handler to remove the sequence manager and add the attract mode to prepare for starting a new game::

	def highscore_entry_finished(self, mode):
	    self.modes.remove(mode)
	    self.start_attract_mode()

An attract mode that displays the high scores might look like this::

	class Attract(game.Mode):
	    def mode_started(self):
	        script = [{'seconds':2.0, 'layer':None}]
	        for frame in highscore.generate_highscore_frames(self.game.highscore_categories):
	            layer = dmd.FrameLayer(frame=frame)
	            script.append({'seconds':2.0, 'layer':layer})
	        self.layer = dmd.ScriptedLayer(width=128, height=32, script=script)

That the ``None`` layer allows the score display to be seen (as it is beneath the attract mode) for one period of the script.


Default Scores
--------------

Default scores and initials should be set using the game data template (the *template_filename* argument to :meth:`procgame.game.GameController.load_game_data`).  The key must match the :attr:`HighScoreCategory.game_data_key` value.  Example::

	ClassicHighScores:
	  - {inits: GSS, score: 5000000}
	  - {inits: ASP, score: 4000000}
	  - {inits: JRP, score: 3000000}
	  - {inits: JAG, score: 2000000}
	  - {inits: JTW, score: 1000000}
	LoopsHighScoreData:
	  - {inits: GSS, score: 5}


Classes
=======

CategoryLogic
-------------

.. autoclass:: procgame.highscore.CategoryLogic
	:members:

EntryPrompt
-----------

.. autoclass:: procgame.highscore.EntryPrompt
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