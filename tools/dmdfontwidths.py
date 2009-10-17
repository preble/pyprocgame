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
sys.path.append(sys.path[0]+'/..') # Set the path so we can find procgame.  We are assuming (stupidly?) that the first member is our directory.
import pinproc
import procgame
from procgame import *
import time

def main():
	if len(sys.argv) < 3:
		print("Usage: %s <font.dmd> <text>"%(sys.argv[0]))
		return

	font = dmd.Font(sys.argv[1])
	if not font:
		print("Error loading font")
		return
	save_path = sys.argv[1]
	text = sys.argv[2]
	
	for i in range(96):
		if font.char_widths[i] != 0:
			print("%s = % 2d" % (chr(i+ord(' ')), font.char_widths[i]))
	
	text_layer = dmd.TextLayer(0, 0, font)
	text_layer.set_text(text)

	proc = pinproc.PinPROC('wpc')
	w = 128
	h = 32
	proc.reset(1)
	
	
	while True:
		grouped_layer = dmd.GroupedLayer(w, h, [dmd.FrameLayer(frame=dmd.Frame(w, h)), text_layer])
		frame = grouped_layer.next_frame()
		if frame == None:
			print("No frame?")
			return
		for x in range(5): # Send it enough times to get it to show
			proc.dmd_draw(frame)
		
		print("Enter character to set: ")
		try:
			chars = sys.stdin.readline()
			if len(chars) == 1:
				print "Got empty line"
				break
			chars = chars[:-1] # Chop off newline
			print("Width for %s" % (chars))
			width = int(sys.stdin.readline())
			for char in chars:
				char_index = ord(char)-ord(' ')
				font.char_widths[char_index] = width
				print("%s => % 2d" % (char, font.char_widths[char_index]))
			print ("Set to %d, text size is now %s" % (width, font.size(text)))
			text_layer.set_text(text) # Force redrawing the text
		except Exception, e:
			print e

	font.save(save_path)

if __name__ == "__main__":
	main()