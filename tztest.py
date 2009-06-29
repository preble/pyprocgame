import procgame
from threading import Thread
import sys

class Attract(procgame.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		procgame.Mode.__init__(self, game, 0)

	def mode_topmost(self):
		self.game.lamps.startButton.schedule(schedule=0x00000fff, cycle_seconds=0, now=False)

	def mode_tick(self):
		if self.game.switches.rocketKickout.is_closed():
			self.game.coils.rocketKickout.pulse(30)
		if self.game.switches.slotKickout.is_closed():
			self.game.coils.slotKickout.pulse(30)
		if self.game.switches.outhole.is_closed():
			self.game.coils.outhole.pulse(50)
	
	def sw_startButton_closed(self):
		print "Got start!"
		self.game.modes.add(StartOfBall(self.game))
		return True


class StartOfBall(procgame.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game):
		procgame.Mode.__init__(self, game, 1)

	def mode_started(self):
		self.game.lamps.startButton.disable()
		if self.game.switches.troughRight.is_closed():
			self.game.coils.ballRelease.pulse(20)
		pass
		
	def sw_troughFarLeft_closed(self):
		in_play = self.game.is_ball_in_play()
		if not in_play:
			rightTrough_closed = self.game.switches.troughRight.is_closed()
			shooterLane_closed = self.game.switches.shooterLane.is_closed()
			if rightTrough_closed and not shooterLane_closed:
				self.game.coils.ballRelease.pulse(20)
		# TODO: What if the ball doesn't make it into the shooter lane?
		#       We should check for it on a later mode_tick() and possibly re-pulse.
		return True
		
	def sw_outhole_closed(self):
		# TODO: End of ball
		self.game.coils.outhole.pulse(20)
		return True
		
	def sw_startButton_closed(self):
		# Todo: Add players to game
		return True
	
	

class TestGame(procgame.GameController):
	"""docstring for TestGame"""
	def __init__(self, machineType):
		procgame.GameController.__init__(self, machineType)
		
	def setup(self):
		"""docstring for setup"""
		self.proc.reset(1)
		self.load_config('../libpinproc/examples/pinproctest/TZ.yaml')
		self.modes.add(Attract(self))
		
	def is_ball_in_play(self):
		return self.switches.troughLeft.is_open() # TODO: Check other trough switches.
		
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