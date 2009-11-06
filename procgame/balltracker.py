from game import *

class BallTracker():
	"""Tracks various ball-related stats."""
	def __init__(self, game, num_balls):
		self.game = game
		self.num_machine_balls = num_balls
		self.num_balls_lost = 0
		self.num_balls_in_play = 0
		self.num_balls_locked = 0

	def ball_drain_action(self):
		# Base future calculations on how many balls the machine thinks are currently
		# installed.
                num_current_machine_balls = self.num_machine_balls - self.num_balls_lost
		if self.game.ball_save.is_active():
			
			# Calculate how many balls shouldn't be in the trough assuming one just drained
			num_balls_out = self.num_balls_locked + (self.game.ball_save.num_balls_to_save -1)
			# Translate that to how many balls should be in the trough if one is being saved.
			balls_in_trough = num_current_machine_balls - num_balls_out
			if self.game.trough.num_balls() >= balls_in_trough:
				return 'save'
			else:
				# If there are too few balls in the trough.  Ignore this one in an attempt to correct the tracking.
				print "Ball tracking error - Incorrect number of balls in trough"
				return 'ignore'
		else:
			num_trough_balls_if_ball_ending = num_current_machine_balls - self.num_balls_locked
			num_trough_balls_if_multiball_ending = num_trough_balls_if_ball_ending - 1
			num_trough_balls_if_multiball_drain = num_trough_balls_if_ball_ending - (self.num_balls_in_play - 1)
			if self.num_balls_in_play == 2:
				if self.game.trough.num_balls() == num_trough_balls_if_multiball_ending:
					return 'end_multiball'
				else:
					return 'ignore'
			elif self.num_balls_in_play == 1:
				if self.game.trough.num_balls() == num_trough_balls_if_ball_ending:
					return 'end_ball'
				else:
					print "Ball tracking error - Incorrect number of balls in trough"
					return 'ignore'
			# Check to see if the number of balls in the trough
			# indicate a ball is newly out of play (rather than the
			# trough switches simply being reactivated do to machine
			# shaking or something).
			elif self.game.trough.num_balls() == num_trough_balls_if_multiball_drain:
				return 'ball_out_of_play'
			
			
class Trough(Mode):
	"""Keeps track of ball save timer."""
	def __init__(self, game):
		super(Trough, self).__init__(game, 90)

	def is_full(self, num_balls=0):
		if num_balls == 0:
			num_balls = self.game.num_balls_total
                if self.game.machineType == 'wpc':
			end_number = 6 - num_balls
			for i in range(6, end_number, -1):
				swName = 'trough' + str(i) 
				if self.game.switches[swName].is_closed():
					return False

			return True
					
		else:
			end_number = 1 + num_balls
			for i in range(1, end_number):
				swName = 'trough' + str(i) 
				if self.game.switches[swName].is_open():
					return False

			return True

	def num_balls(self):
		ball_count = 0
                if self.game.machineType == 'wpc':
			end_number = 6 - self.game.num_balls_total
			for i in range(6, end_number, -1):
				swName = 'trough' + str(i) 
				if self.game.switches[swName].is_active():
					ball_count += 1

			return ball_count
					
		else:
			end_number = 1 + self.game.num_balls_total
			for i in range(1, end_number):
				swName = 'trough' + str(i) 
				if self.game.switches[swName].is_active():
					ball_count += 1

			return ball_count

