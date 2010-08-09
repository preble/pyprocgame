from ..game import Mode

class Replay(Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Replay, self).__init__(game, priority)
		self.replay_achieved = [False, False, False, False]
		self.replay_scores = [500000,600000,700000,800000]
		self.num_replay_levels = 1
		self.replay_callback = 'None'

	def mode_started(self):

		self.replay_type = self.game.user_settings['Replay']['Replay Type']
		if self.replay_type == 'auto':
			self.num_levels = 1
		else:
			self.num_levels = self.game.user_settings['Replay']['Replay Levels']
		self.replay_percentage = float(self.game.user_settings['Replay']['Replay Percentage'])
		self.replay_boost = self.game.user_settings['Replay']['Replay Boost']
		self.default_scores = [self.game.user_settings['Replay']['Replay Level 1'],
		                       self.game.user_settings['Replay']['Replay Level 2'],
		                       self.game.user_settings['Replay']['Replay Level 3'],
		                       self.game.user_settings['Replay']['Replay Level 4']]


		self.set_replay_scores()
		replay_on = self.replay_type != 'none'
		score = self.game.current_player().score
		for i in range(0,4):
			# Set already achieved if replay is off, level not active, or
			# score is higher
			self.replay_achieved[i] = not replay_on or self.num_levels <= i or score > self.replay_scores[i]
		for i in range(0,4):
			# Schedule the score check if any level hasn't been achieved yet.
			if not self.replay_achieved[i]:
				self.delay(name='replay_check', event_type=None, delay=0.3, handler=self.replay_check)
				break

		print "Replay scores: %s" % self.replay_scores
		print "Replay achieved: %s" % self.replay_achieved
		print "levels: %s" % self.num_levels
			
	def set_replay_scores(self):
		if self.replay_type == 'auto':
			self.replay_scores[0] = self.calc_auto_replay_score()
			if self.replay_scores[0] < self.default_scores[0]:
				self.replay_scores[0] = self.default_scores[0]
		elif self.replay_type == 'fixed':
			for i in range(0,4):
				self.replay_scores[i] = self.default_scores[i]
		elif self.replay_type == 'incremental':
			self.replay_scores[0] = self.default_scores[0]
			for i in range(1,4):
				self.replay_scores[i] = self.replay_scores[i-1] + self.replay_boost

	def calc_auto_replay_score(self):
		return (int(int(self.game.game_data['Audits']['Avg Score']) * ((100.0-self.replay_percentage) / 100)) / 10000) * 10000

	def mode_stopped(self):
		self.cancel_delayed('replay_check')

	def replay_check(self):
		index = 3
		for i in range(0,4):
			if not self.replay_achieved[i]:
				index = i
				break
		if not self.replay_achieved[index]:
			if self.game.current_player().score > self.replay_scores[index]:
				if self.replay_callback != 'None':
					self.replay_callback()
				self.replay_achieved[index] = True
				if self.num_levels > index:
					self.delay(name='replay_check', event_type=None, delay=0.3, handler=self.replay_check)
			else: 
				self.delay(name='replay_check', event_type=None, delay=0.3, handler=self.replay_check)
		
