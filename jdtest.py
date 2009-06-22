from procgame import procgame # This is kinda goofy.
from threading import Thread
import sys
import random
import string
import time

class Attract(procgame.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		procgame.Mode.__init__(self, game, 1)

	def mode_topmost(self):
		self.game.lamps.gi01.schedule(schedule=0xffffffff, cycle_seconds=0, now=False)
		self.game.lamps.gi02.disable()
		self.game.lamps.startButton.schedule(schedule=0x00000fff, cycle_seconds=0, now=False)
		self.game.set_status("Press Start")

	def mode_tick(self):
		if self.game.switches.shooterL.is_closed():
			self.game.coils.shooterL.pulse(50)
		if self.game.switches.shooterR.is_closed():
			self.game.coils.shooterR.pulse(50)
		if self.game.switches.popperL.is_open(seconds=1.0): # opto!
			self.game.switches.popperL.reset_timer()
			print("bam")
			# We can't do this like this because 
			self.game.coils.popperL.pulse(20) # BAD!!!
		if self.game.switches.popperR.is_open(seconds=1.0): # opto!
			self.game.switches.popperR.reset_timer()
			print("bam2")
			# We can't do this like this because 
			self.game.coils.popperR.pulse(20) # BAD!!!

	def sw_startButton_closed(self):
		self.game.set_status("Got start!")
		self.game.modes.add(StartOfBall(self.game))
		self.game.modes.remove(self)
		return True


class StartOfBall(procgame.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		procgame.Mode.__init__(self, game, 2)

	def mode_started(self):
		self.game.lamps.gi02.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
		self.game.lamps.startButton.disable()
		if self.game.switches.trough6.is_open():
			self.game.set_status("Pulsing trough")
			self.game.coils.trough.pulse(20)
		pass
		
	def mode_tick(self):
		if self.game.switches.popperL.is_open(seconds=1.0): # opto!
			self.game.switches.popperL.reset_timer()
			print("bam3")
			# We can't do this like this because 
			self.game.coils.popperL.pulse(20) # BAD!!!
		if self.game.switches.popperR.is_open(seconds=1.0): # opto!
			self.game.switches.popperR.reset_timer()
			print("bam4")
			# We can't do this like this because 
			self.game.coils.popperR.pulse(20) # BAD!!!
	
	def sw_trough1_open(self):
		in_play = self.game.is_ball_in_play()
		if not in_play:
			self.game.set_status("Ball dropped")
			trough6_closed = self.game.switches.trough6.is_open()
			shooterR_closed = self.game.switches.shooterR.is_closed()
			if trough6_closed and not shooterR_closed:
				self.game.set_status("Pulsing next ball")
				self.game.coils.trough.pulse(20)
		# TODO: What if the ball doesn't make it into the shooter lane?
		#       We should check for it on a later mode_tick() and possibly re-pulse.
		return True
		
	def sw_startButton_closed(self):
		# Todo: Add players to game
		return True
	
	def sw_fireL_closed(self):
		if self.game.switches.shooterL.is_closed():
			self.game.coils.shooterL.pulse(50)
	
	def sw_fireR_closed(self):
		if self.game.switches.shooterR.is_closed():
			self.game.coils.shooterR.pulse(50)
	
class DMDStatus(procgame.Mode):
	"""docstring for DMDStatus"""
	def __init__(self, game):
		procgame.Mode.__init__(self, game, 0)
		self.frame = self.create_frame()
		self.font = self.create_frame()
		f = open('font5x6.dmd', 'r')
		font_data = f.read()[1:]
		for col in range(128):
			for row in range(32):
				#print("%d, %d" % (col, row))
				self.font[col][row] = ord(font_data[col+(row*128)])*60
	
	def create_frame(self):
		frame = []
		for x in range(128):
			frame += [[0] * 32]
		return frame
	
	def clear(self):
		self.frame = self.create_frame()
	
	def update(self):
		f = ""
		# for col in self.frame:
		# 	for pixel in col:
		# 		f += chr(pixel)*4
		for y in range(32):
			for x in range(128):
				f += chr(self.frame[x][y])*4
		self.game.proc.dmd_draw(f)
	
	def draw_text(self, text, position = (0, 0)):
		
		framex = 0
		text = string.upper(text)
		for ch in text:
			if (ch >= 'A') and (ch <= 'Z'):
				bitmapy = 0
				bitmapx = (ord(ch)-ord('A')) * 5
			elif (ch >= '0') and (ch <= '9'):
				bitmapy = 6
				bitmapx = (ord(ch)-ord('0')) * 5
			elif (ch >= ' ') and (ch <= '/'):
				bitmapy = 12
				bitmapx = (ord(ch)-ord(' ')) * 5
			else:
				continue
			for x in range(5):
				for y in range(6):
					if (x < 128) and (y < 32):
						self.frame[framex + x + position[0]][0 + y + position[1]] = self.font[bitmapx+x][bitmapy+y]
			framex += 5
			if framex + 5 >= 128:
				break
		self.update()
		
	def mode_tick(self):
		#self.frame[random.randint(0, 127)][random.randint(0, 31)] = random.randint(0, 255)
		if len(self.game.modes.modes) > 0:
			self.draw_text('Topmost- '+str(self.game.modes.modes[0].status_str()), (0,0))
		# for y in range(4):
		# 	self.draw_text("Hello! "+str(time.time()), (0, y*6+6))
		#self.draw_text("Adam was here...", (0, 20))

class TestGame(procgame.GameController):
	"""docstring for TestGame"""
	def __init__(self, machineType):
		procgame.GameController.__init__(self, machineType)
		self.dmdstatus = DMDStatus(self)
		
	def setup(self):
		"""docstring for setup"""
		self.proc.reset(1)
		self.load_config('../libpinproc/examples/pinproctest/JD.yaml')
		print("Initial switch states:")
		for sw in self.switches:
			print("  %s:\t%s" % (sw.name, sw.state_str()))
		self.modes.add(self.dmdstatus)
		self.modes.add(Attract(self))
		
	def is_ball_in_play(self):
		return self.switches.trough1.is_closed() # TODO: Check other trough switches.
	
	def set_status(self, text):
		self.dmdstatus.draw_text('Last- '+text, (0, 6))
		print(text)
		
def main():
	machineType = 'wpc'
	game = None
	try:
	 	game = TestGame(machineType)
		game.setup()
		game.run_loop()
	finally:
		del game

if __name__ == '__main__': main()