import math
from ..game import Mode
from .. import dmd
 
class InitialEntryMode(Mode):
	"""Mode that prompts the player for their initials.
	
	*left_text* and *right_text* are strings or arrays to be displayed at the
	left and right corners of the display.  If they are arrays they will be
	rotated.
	
	:attr:`entered_handler` is called once the initials have been confirmed.
	
	This mode does not remove itself; this should be done in *entered_handler*."""
	
	entered_handler = None
	"""Method taking two parameters: `mode` and `inits`."""
	
	char_back = '<'
	char_done = '='
	
	init_font = None
	font = None
	letters_font = None
	
	def __init__(self, game, priority, left_text, right_text, entered_handler):
		super(InitialEntryMode, self).__init__(game, priority)
		
		self.entered_handler = entered_handler
		
		self.init_font = dmd.font_named('Font09Bx7.dmd')
		self.font = dmd.font_named('Font07x5.dmd')
		self.letters_font = dmd.font_named('Font07x5.dmd')
		
		self.layer = dmd.GroupedLayer(128, 32)
		self.layer.opaque = True
		self.layer.layers = []
		
		if type(right_text) != list:
			right_text = [right_text]
		if type(left_text) != list:
			left_text = [left_text]
		
		seconds_per_text = 1.5
		
		script = []
		for text in left_text:
			frame = dmd.Frame(width=128, height=8)
			self.font.draw(frame, text, 0, 0)
			script.append({'seconds':seconds_per_text, 'layer':dmd.FrameLayer(frame=frame)})
		topthird_left_layer = dmd.ScriptedLayer(width=128, height=8, script=script)
		topthird_left_layer.composite_op = 'blacksrc'
		self.layer.layers += [topthird_left_layer]
		
		script = []
		for text in right_text:
			frame = dmd.Frame(width=128, height=8)
			self.font.draw(frame, text, 128-(self.font.size(text)[0]), 0)
			script.append({'seconds':seconds_per_text, 'layer':dmd.FrameLayer(frame=frame)})
		topthird_right_layer = dmd.ScriptedLayer(width=128, height=8, script=script)
		topthird_right_layer.composite_op = 'blacksrc'
		self.layer.layers += [topthird_right_layer]
		
		self.inits_frame = dmd.Frame(width=128, height=10)
		inits_layer = dmd.FrameLayer(opaque=False, frame=self.inits_frame)
		inits_layer.set_target_position(0, 11)
		self.layer.layers += [inits_layer]
		
		self.lowerhalf_layer = dmd.FrameQueueLayer(opaque=False, hold=True)
		self.lowerhalf_layer.set_target_position(0, 24)
		self.layer.layers += [self.lowerhalf_layer]
		
		self.letters = []
		for idx in range(26):
			self.letters += [chr(ord('A')+idx)]
		self.letters += [' ', '.', self.char_back, self.char_done]
		self.current_letter_index = 0
		self.inits = self.letters[self.current_letter_index]
		self.animate_to_index(0)
	
	def mode_started(self):
		pass
		
	def mode_stopped(self):
		pass
				
	def animate_to_index(self, new_index, inc = 0):
		letter_spread = 10
		letter_width = 7
		if inc < 0:
			rng = range(inc * letter_spread, 1)
		elif inc > 0:
			rng = range(inc * letter_spread)[::-1]
		else:
			rng = [0]
		#print rng
		for x in rng:
			frame = dmd.Frame(width=128, height=10)
			for offset in range(-7, 8):
				index = new_index - offset
				#print "Index %d  len=%d" % (index, len(self.letters))
				if index < 0:
					index = len(self.letters) + index
				elif index >= len(self.letters):
					index = index - len(self.letters)
				(w, h) = self.font.size(self.letters[index])
				#print "Drawing %d w=%d" % (index, w)
				self.letters_font.draw(frame, self.letters[index], 128/2 - offset * letter_spread - letter_width/2 + x, 0)
			frame.fill_rect(64-5, 0, 1, 10, 1)
			frame.fill_rect(64+5, 0, 1, 10, 1)
			self.lowerhalf_layer.frames += [frame]
		self.current_letter_index = new_index
		
		# Prune down the frames list so we don't get too far behind while animating
		x = 0
		while len(self.lowerhalf_layer.frames) > 15 and x < (len(self.lowerhalf_layer.frames)-1):
			del self.lowerhalf_layer.frames[x]
			x += 2
		
		# Now draw the top right panel, with the selected initials in order:
		self.inits_frame.clear()
		init_spread = 8
		x_offset = self.inits_frame.width/2 - len(self.inits) * init_spread / 2
		for x in range(len(self.inits)):
			self.init_font.draw(self.inits_frame, self.inits[x], x * init_spread + x_offset, 0)
		self.inits_frame.fill_rect((len(self.inits)-1) * init_spread + x_offset, 9, 8, 1, 1)
		
	def letter_increment(self, inc):
		new_index = (self.current_letter_index + inc)
		if new_index < 0:
			new_index = len(self.letters) + new_index
		elif new_index >= len(self.letters):
			new_index = new_index - len(self.letters)
		#print("letter_increment %d + %d = %d" % (self.current_letter_index, inc, new_index))
		self.inits = self.inits[:-1] + self.letters[new_index]
		self.animate_to_index(new_index, inc)
	
	def letter_accept(self):
		# TODO: Add 'back'/erase/end
		letter = self.letters[self.current_letter_index]
		if letter == self.char_back:
			if len(self.inits) > 0:
				self.inits = self.inits[:-1]
		elif letter == self.char_done or len(self.inits) > 10:
			self.inits = self.inits[:-1] # Strip off the done character
			if self.entered_handler != None:
				self.entered_handler(mode=self, inits=self.inits)
			else:
				self.game.logger.warning('InitialEntryMode finished but no entered_handler to notify!')
		else:
			self.inits += letter
		self.letter_increment(0)
	
	def sw_flipperLwL_active(self, sw):
		self.periodic_left()
		return False
	def sw_flipperLwL_inactive(self, sw):
		self.cancel_delayed('periodic_movement')
		
	def sw_flipperLwR_active(self, sw):
		self.periodic_right()
		return False
	def sw_flipperLwR_inactive(self, sw):
		self.cancel_delayed('periodic_movement')
		
	def periodic_left(self):
		self.letter_increment(-1)
		self.delay(name='periodic_movement', event_type=None, delay=0.2, handler=self.periodic_left)
	def periodic_right(self):
		self.letter_increment(1)
		self.delay(name='periodic_movement', event_type=None, delay=0.2, handler=self.periodic_right)
		
	def sw_startButton_active(self, sw):
		self.letter_accept()
		return True
