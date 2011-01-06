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
from procgame import dmd
import time

def dmdfontwidths(font_path, text):
	font = dmd.Font(font_path)
	if not font:
		print("Error loading font")
		return False
	
	for i in range(96):
		if font.char_widths[i] != 0:
			print("%s = % 2d" % (chr(i+ord(' ')), font.char_widths[i]))
	
	text_layer = dmd.TextLayer(0, 0, font)
	text_layer.set_text(text)

	proc = pinproc.PinPROC(pinproc.MachineTypeWPC) # TODO: Make this an option!
	w = 128
	h = 32
	proc.reset(1)
	
	
	while True:
		grouped_layer = dmd.GroupedLayer(w, h, [dmd.FrameLayer(frame=dmd.Frame(w, h)), text_layer])
		frame = grouped_layer.next_frame()
		if frame == None:
			print("No frame?")
			return True
		#for x in range(5): # Send it enough times to get it to show
		proc.dmd_draw(frame)
		
		print("Enter character to set: ")
		try:
			chars = sys.stdin.readline()
			if len(chars) == 1:
				print "Got empty line"
				break
			chars = chars[:-1] # Chop off newline
			for char in chars:
				char_index = ord(char)-ord(' ')
				print("Current width of %s is % 2d" % (char, font.char_widths[char_index]))
			#print("Width for %s (now %d):" % (chars, font.char_widths[char_index]))
			width = int(sys.stdin.readline())
			for char in chars:
				char_index = ord(char)-ord(' ')
				font.char_widths[char_index] = width
				print("%s => % 2d" % (char, font.char_widths[char_index]))
			print ("Set to %d, text size is now %s" % (width, font.size(text)))
			text_layer.set_text(text) # Force redrawing the text
		except Exception, e:
			print e

	font.save(font_path)
	return True


def tool_populate_options(parser):
    pass

def tool_get_usage():
    return """<font.dmd> <text>"""

def tool_run(options, args):
    if len(args) < 2:
        return False
    return dmdfontwidths(font_path=args[0], text=args[1])
