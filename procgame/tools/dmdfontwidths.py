#  dmdfondwidths.py
#  Helper tool for setting character widths on P-ROC .dmd-based fonts.
#  
#  Opens the given .dmd font file and displays the given text on the DMD with that font.
#  Type in a character (or set of characters), hit return, then type the width of that character (or set of characters).
#  The DMD will be updated to display the text with the new character width properties.  Hit enter at the character
#  prompt to save to the .dmd file and exit the program.
#
import sys
import os
import pinproc
from procgame import game
from procgame import dmd
import time

class DmdFontWidthsGame(game.BasicGame):
	def __init__(self, font, font_path, text):
		super(DmdFontWidthsGame, self).__init__(pinproc.MachineTypeCustom)
		self.reset()
		w = 128
		h = 32
		self.font = font
		self.font_path = font_path
		self.text = text
		self.text_layer = dmd.TextLayer(0, 0, font)
		self.text_layer.set_text(text)
		mode = game.Mode(game=self, priority=9)
		mode.layer = dmd.GroupedLayer(w, h, [dmd.FrameLayer(frame=dmd.Frame(w, h)), self.text_layer])
		self.modes.add(mode)
		self.dirty = False
	
	def show_last_frame(self):
		# Override BasicGame's show_last_frame() in order to pause and wait for user input.
		# This means that the game loop only runs after each user input.
		if self.desktop and self.last_frame:
			self.desktop.draw(self.last_frame)
			self.last_frame = None
			print "Enter character(s) to set width of: ",
			try:
				chars = sys.stdin.readline()
				if len(chars) == 1:
					print "Got empty line; exiting."
					if self.dirty:
						print "Saving font to %s" % (self.font_path)
						self.font.save(self.font_path)
					else:
						print "No changes."
					self.end_run_loop()
					return
				chars = chars[:-1] # Chop off newline
				for char in chars:
					char_index = ord(char)-ord(' ')
					print("Current width of %s is %d" % (char, self.font.char_widths[char_index]))
				print "Enter new width for characters: ",
				width = int(sys.stdin.readline())
				for char in chars:
					char_index = ord(char)-ord(' ')
					self.font.char_widths[char_index] = width
					print("%s => % 2d" % (char, self.font.char_widths[char_index]))
				print ("Set to %d, text size is now %s" % (width, self.font.size(self.text)))
				self.text_layer.set_text(self.text) # Force redrawing the text
				self.dirty = True
			except Exception, e:
				print e

def tool_populate_options(parser):
	pass

def tool_get_usage():
	return """<font.dmd> <text>"""

def tool_run(options, args):
	if len(args) != 2:
		return False

	font_path, text = args

	font = dmd.Font(font_path)
	if not font:
		print("Error loading font")
		return False

	print("Enter with no input exits and saves changes.")
	game = DmdFontWidthsGame(font, font_path, text)
	game.run_loop()
	return True
