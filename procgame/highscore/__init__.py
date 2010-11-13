__all__ = [
	'category',
	'entry',
	'sequence',
	]

from category import *
from entry import *
from sequence import *

import time
import locale
from .. import dmd


def generate_highscore_frames(categories):
	"""Utility function that returns a sequence of :class:`~procgame.dmd.Frame` objects
	describing the current high scores in each of the *categories* supplied.
	*categories* should be a list of :class:`HighScoreCategory` objects.
	"""
	markup = dmd.MarkupFrameGenerator()
	frames = list()
	for category in categories:
		for index, score in enumerate(category.scores):
			score_str = locale.format("%d", score.score, True) # Add commas to the score.
			if score.score == 1:
				score_str += category.score_suffix_singular
			else:
				score_str += category.score_suffix_plural
			text = '[%s]\n#%s#\n[%s]' % (category.titles[index], score.inits, score_str)
			frame = markup.frame_for_markup(markup=text, y_offset=4)
			frames.append(frame)
	return frames
