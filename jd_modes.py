import procgame
from procgame import *
from random import *

class Scoring_Mode(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Scoring_Mode, self).__init__(game, priority)
		self.bonus_base_elements = {}
		self.bonus_base_elements['modes_attempted'] = 0
		self.bonus_x = 0

class Bonus(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, font_big, font_small):
		super(Bonus, self).__init__(game, priority)
		self.font_big = font_big
		self.font_small = font_small
		self.title_layer = dmd.TextLayer(128/2, 7, font_big, "center")
		self.element_layer = dmd.TextLayer(128/2, 7, font_small, "center")
		self.value_layer = dmd.TextLayer(128/2, 20, font_small, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.title_layer,self.element_layer, self.value_layer])
		self.timer = 0
		self.delay_time = 1

	def compute(self, base, x, exit_function):
		self.exit_function = exit_function
		self.elements = []
		self.value = []
		print "base"
		print base
		for element, value in base.iteritems():
			self.elements.append(element)
			self.value.append(value)
		self.x = x
		self.delay(name='bonus_computer', event_type=None, delay=self.delay_time, handler=self.bonus_computer)
		self.title_layer.set_text('BONUS:',self.delay_time)
		self.total_base = 0
		self.game.dmd.layers.append(self.layer)

	def bonus_computer(self):
		self.title_layer.set_text('')
		self.element_layer.set_text(self.elements[self.timer])
		self.value_layer.set_text(str(self.value[self.timer]))
		self.total_base += self.value[self.timer]
		self.timer += 1

		if self.timer == len(self.elements) or len(self.elements) == 0:
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
			self.timer = 0
		else:
			self.delay(name='bonus_computer', event_type=None, delay=self.delay_time, handler=self.bonus_computer)

	def bonus_finish(self):
		if self.timer == 0:
			self.element_layer.set_text('Total Base:')
			self.value_layer.set_text(str(self.total_base))
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		elif self.timer == 1:
			self.element_layer.set_text('Multiplier:')
			self.value_layer.set_text(str(self.x))
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		elif self.timer == 2:
			total_bonus = self.total_base * self.x
			self.element_layer.set_text('Total Bonus:')
			self.value_layer.set_text(str(total_bonus))
			self.game.score(total_bonus)
			self.delay(name='bonus_finish', event_type=None, delay=self.delay_time, handler=self.bonus_finish)
		else:
			self.game.dmd.layers.remove(self.layer)
			self.exit_function()
		self.timer += 1

	def sw_flipperLwL_active(self, sw):
		if self.game.switches.flipperLwR.is_active():
			self.delay_time = 0.250

	def sw_flipperLwR_active(self, sw):
		if self.game.switches.flipperLwL.is_active():
			self.delay_time = 0.250

class JD_Modes(Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, font):
		super(JD_Modes, self).__init__(game, priority)
		self.reset()
		self.mode_timer = ModeTimer(game, priority+1)
		self.mode_pursuit = Pursuit(game, priority+1)
		self.mode_blackout = Blackout(game, priority+1)
		self.mode_sniper = Sniper(game, priority+1)
		self.mode_battleTank = BattleTank(game, priority+1)
		self.mode_impersonator = Impersonator(game, priority+1)
		self.mode_meltdown = Meltdown(game, priority+1)
		self.mode_safecracker = Safecracker(game, priority+1)
		self.mode_manhunt = ManhuntMillions(game, priority+1)
		self.mode_stakeout = Stakeout(game, priority+1)
		self.font = font
		self.crimescenes = Crimescenes(game, priority+1)
		self.num_modes_for_extra_ball = [3,7]

	def reset(self):
		self.state = 'idle'
		self.judges_attempted = []
		self.judges_not_attempted = ['Fear', 'Mortis', 'Death', 'Fire']
		self.modes_attempted = []
		self.modes_not_attempted = ['pursuit', 'blackout', 'sniper', 'battleTank', 'impersonator', 'meltdown', 'safecracker', 'manhunt', 'stakeout']
		self.modes_just_attempted = []
		self.active_mode_pointer = 0
		self.multiball_active = False
		self.multiball_jackpot_collected = False
		self.modes_not_attempted_ptr = 0
		self.mode_active = False
		self.mode_list = {}
		self.mode = 0
		self.extra_balls_lit = 0
		self.two_ball_active = False
		self.mystery_lit = False
		self.missile_award_lit = False
		self.num_modes_completed = 0
		for mode in self.modes_not_attempted:
			self.drive_mode_lamp(mode, 'off')
		self.drive_mode_lamp('mystery', 'off')
		for judge in self.judges_not_attempted:
			self.game.coils['flasher' + judge].disable()

	def mode_started(self):
		self.mode_timer.callback = self.mode_over
		self.mode_list['pursuit'] = self.mode_pursuit
		self.mode_list['blackout'] = self.mode_blackout
		self.mode_list['sniper'] = self.mode_sniper
		self.mode_list['battleTank'] = self.mode_battleTank
		self.mode_list['impersonator'] = self.mode_impersonator
		self.mode_list['meltdown'] = self.mode_meltdown
		self.mode_list['safecracker'] = self.mode_safecracker
		self.mode_list['manhunt'] = self.mode_manhunt
		self.mode_list['stakeout'] = self.mode_stakeout
		for mode in self.mode_list:
			self.mode_list[mode].callback = self.mode_over
		self.crimescenes.light_extra_ball_function = self.light_extra_ball
		self.game.modes.add(self.mode_timer)
		self.game.modes.add(self.crimescenes)

	def mode_stopped(self):
		self.game.modes.remove(self.mode_timer)
		self.game.modes.remove(self.crimescenes)
		if self.mode_active:
			this_mode = self.mode_list[self.mode]
			self.game.modes.remove(self.mode_list[self.mode])
			

	def get_info_record(self):
		info_record = {}
		info_record['state'] = self.state
		info_record['judges_attempted'] = self.judges_attempted
		info_record['judges_not_attempted'] = self.judges_not_attempted
		info_record['mode'] = self.mode
		info_record['modes_attempted'] = self.modes_attempted
		info_record['modes_just_attempted'] = self.modes_just_attempted
		info_record['modes_not_attempted'] = self.modes_not_attempted
		info_record['modes_not_attempted_ptr'] = self.modes_not_attempted_ptr
		info_record['multiball_jackpot_collected'] = self.multiball_jackpot_collected
		info_record['extra_balls_lit'] = self.extra_balls_lit
		info_record['mystery_lit'] = self.mystery_lit
		info_record['missile_award_lit'] = self.missile_award_lit
		info_record['num_modes_completed'] = self.num_modes_completed
		info_record['crimescenes'] = self.crimescenes.get_info_record()
		return info_record

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.state = info_record['state']
			self.mode= info_record['mode']
			self.modes_attempted = info_record['modes_attempted']
			self.modes_just_attempted = info_record['modes_just_attempted']
			self.modes_not_attempted = info_record['modes_not_attempted']
			self.modes_not_attempted_ptr = info_record['modes_not_attempted_ptr']
			self.multiball_jackpot_collected = info_record['multiball_jackpot_collected']
			self.judges_attempted = info_record['judges_attempted']
			self.judges_not_attempted = info_record['judges_not_attempted']
			self.extra_balls_lit = info_record['extra_balls_lit']
			self.mystery_lit = info_record['mystery_lit']
			self.missile_award_lit = info_record['missile_award_lit']
			self.num_modes_completed = info_record['num_modes_completed']
			self.crimescenes.update_info_record(info_record['crimescenes'])
			print "modes attempted"
			print self.modes_attempted
		else:	
			self.crimescenes.update_info_record({})
		
		self.begin_processing()

	def light_extra_ball(self):
		self.extra_balls_lit += 1
		self.enable_extra_ball()

	def enable_extra_ball(self):
		self.drive_mode_lamp('extraBall2','on')

	def get_bonus_base(self):
		bonus_base_elements = self.bonus_base_elements.copy()
		print self.bonus_base_elements 
		print self.crimescenes.bonus_base_elements
		bonus_base_elements.update(self.crimescenes.bonus_base_elements)
		print "bonus_base_elements"
		print bonus_base_elements
		print "hi"
		return bonus_base_elements

	def get_bonus_x(self):
		return 1

	def begin_processing(self):
		for judge in self.judges_attempted:
			self.game.coils['flasher' + judge].disable()
		for mode in self.modes_attempted:
			self.drive_mode_lamp(mode, 'on')
		if self.state == 'idle':
			self.setup_next_mode()
		elif self.state == 'pre_ultimate_challenge':
			self.setup_ultimate_challenge()
		elif self.state == 'pre_judge_battle':
			self.setup_judge_battle()
		elif self.state == 'mode':
			self.mode_complete()
		elif self.state == 'judge_battle':
			self.judge_battle_complete()
		elif self.state == 'ultimate_battle':
			self.ultimate_battle_complete()
		if self.extra_balls_lit > 0:
			self.enable_extra_ball()
		if self.mystery_lit:
			self.drive_mode_lamp('mystery', 'on')


	def rotate_modes(self, adder):
		self.disable_not_attempted_mode_lamps()
		self.active_mode_pointer += adder
		self.modes_not_attempted_ptr = self.active_mode_pointer % len(self.modes_not_attempted)
		print "mode_ptr"
		print self.modes_not_attempted_ptr
		if not self.mode_active:
			self.drive_mode_lamp(self.modes_not_attempted[self.modes_not_attempted_ptr],'slow')

	def disable_not_attempted_mode_lamps(self):
		for mode in self.modes_not_attempted:
			self.game.lamps[mode].disable()

	def drive_mode_lamp(self, lamp_name, style='on'):
		if style == 'slow':
			self.game.lamps[lamp_name].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		elif style == 'on':
			self.game.lamps[lamp_name].pulse(0)
		elif style == 'off':
			self.game.lamps[lamp_name].disable()

	def sw_leftScorePost_active(self, sw):
		if self.extra_balls_lit > 0:
			self.award_extra_ball()

	def sw_rightTopPost_active(self, sw):
		if self.extra_balls_lit > 0:
			self.award_extra_ball()

	def sw_mystery_active(self, sw):
		if self.mystery_lit:
			if self.multiball_active or self.two_ball_active:
				self.mystery_lit = False
				self.drive_mode_lamp('mystery', 'off')
				if self.game.start_of_ball_mode.ball_save.timer > 0:
					self.game.set_status('+10 second ball saver')
					self.game.start_of_ball_mode.ball_save.add(10)
				else:
					if self.multiball_active:
						self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=3, time=10, now=True, allow_multiple_saves=True)
					else:
						self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=2, time=10, now=True, allow_multiple_saves=True)
				
			elif self.state == 'mode':
				self.mode_timer.add(10)
				self.game.set_status('Adding 10 seconds')
				self.mystery_lit = False
				self.drive_mode_lamp('mystery', 'off')
			else:
				self.game.set_status('Missile Launch enabled')
				self.missile_award_lit = True

	def award_extra_ball(self):
		self.game.extra_ball()
		self.extra_balls_lit -= 1
		print "extra balls_lit"
		print self.extra_balls_lit
		if self.extra_balls_lit == 0:
			self.drive_mode_lamp('extraBall2','off')
		self.game.set_status('Extra Ball!')

	def sw_fireR_active(self, sw):
		if not self.multiball_active and self.state == 'idle' and self.game.switches.shooterR.is_inactive():
			self.game.set_status("hi")
			self.rotate_modes(1)
		else:
			print "hello"
			print self.state
			print self.multiball_active
			self.game.set_status("hello")

	def sw_fireL_active(self, sw):
		if not self.multiball_active and self.state == 'idle' and self.game.switches.shooterL.is_inactive():
			self.rotate_modes(-1)

	def sw_popperR_active_for_500ms(self, sw):
		if not self.multiball_active:
			if self.state == 'idle':
				self.game.lamps.rightStartFeature.disable()
				self.play_intro = PlayIntro(self.game, self.priority+1, self.modes_not_attempted[self.modes_not_attempted_ptr], self.activate_mode, self.modes_not_attempted[0], self.font)
				self.game.modes.add(self.play_intro)
			elif self.state == 'pre_judge_battle':
				self.game.lamps.rightStartFeature.disable()
				self.play_intro = PlayIntro(self.game, self.priority+1, self.judges_not_attempted[0], self.activate_mode, self.judges_not_attempted[0], self.font)
				self.game.modes.add(self.play_intro)
			elif self.state == 'pre_ultimate_challenge':
				self.game.lamps.rightStartFeature.disable()
				self.play_intro = PlayIntro(self.game, self.priority+1, 'ultimate_challenge', self.activate_mode, 'ultimate_challenge', self.font)
				self.game.modes.add(self.play_intro)
			else:
				self.popperR_launch()
		else:
			self.popperR_launch()

	def activate_mode(self, mode):
		self.game.modes.remove(self.play_intro)
		self.popperR_launch()
		
		if self.state == 'idle':
			self.game.lamps[self.modes_not_attempted[self.modes_not_attempted_ptr]].schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
			self.mode = self.modes_not_attempted[self.modes_not_attempted_ptr]
			print "self.mode"
			print self.mode
			if self.mode == 'impersonator' or self.mode == 'safecracker':
				self.game.start_of_ball_mode.multiball.drops.paused = True
			self.modes_not_attempted.remove(self.mode)
			self.modes_attempted.append(self.mode)
			self.modes_just_attempted.append(self.mode)
			self.state = 'mode'
			self.game.modes.add(self.mode_list[self.mode])
			self.mode_timer.start(25)
			self.mode_active = True
			self.drive_mode_lamp('mystery', 'on')
			self.mystery_lit = True
			
		elif self.state == 'pre_judge_battle':
			self.game.start_of_ball_mode.multiball.drops.paused = True
                        # Start modes from self.modes_just_attempted
			judge = self.judges_not_attempted[0]
			self.judges_not_attempted.remove(judge)
			self.judges_attempted.append(judge)
			self.game.set_status('battle in progress')
			self.state = 'judge_battle'
			for mode in self.modes_attempted:
				self.drive_mode_lamp(mode, 'off')
			for mode in self.modes_just_attempted:
				self.drive_mode_lamp(mode, 'slow')
			self.modes_just_attempted = []
			# Start 2-ball multiball
			self.main_launch()
			self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=2, time=10, now=False, allow_multiple_saves=True)
			self.two_ball_active = True
			self.drive_mode_lamp('mystery', 'on')
			self.mystery_lit = True
			
			
		elif self.state == 'pre_ultimate_challenge':
			self.game.set_status('challenge in progress')
			self.state = 'ultimate_challenge'
			self.drive_mode_lamp('mystery', 'on')
			self.mystery_lit = True

	def setup_next_mode(self):
		if not self.multiball_active:
			self.drive_mode_lamp(self.modes_not_attempted[self.modes_not_attempted_ptr],'slow')
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def setup_judge_battle(self):
		self.state = 'pre_judge_battle'
		if not self.multiball_active:
			self.game.coils['flasher' + self.judges_not_attempted[0]].schedule(schedule=0x00000003, cycle_seconds=0, now=True)
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def setup_ultimate_challenge(self):
		self.state = 'pre_ultimate_challenge'
		if not self.multiball_active:
			self.game.lamps.ultChallenge.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def multiball_started(self):
		self.game.lamps.rightStartFeature.disable()
		self.multiball_active = True
		self.drive_mode_lamp('mystery', 'on')
		self.mystery_lit = True

	def jackpot_collected(self):
		self.multiball_jackpot_collected = True

	def multiball_ended(self):
		self.multiball_active = False
		if self.state == 'idle':
			self.setup_next_mode()
		elif self.state == 'pre_ultimate_challenge':
			self.setup_ultimate_challenge()
		elif self.state == 'pre_judge_battle':
			self.setup_judge_battle()
		elif self.state == 'judge_battle':
			self.judge_battle_complete()

	def end_two_ball(self):
		self.two_ball_active = False
		self.game.start_of_ball_mode.multiball.drops.paused = False
		if not self.multiball_active:
			self.judge_battle_complete()

	def mode_over(self):
		if self.mode_timer.timer > 0:
			self.mode_timer.stop()
		self.mode_active = False
		this_mode = self.mode_list[self.mode]
		success = this_mode.completed
		self.game.modes.remove(self.mode_list[self.mode])
		if self.state == 'mode':
			self.mode_complete(success)	
		elif self.state == 'judge_battle':
			self.judge_battle_complete()	
		elif self.state == 'ultimate_challenge':
			self.ultimate_challenge_complete()	

		self.mode_complete()

	def mode_complete(self, successful=False):
		self.game.start_of_ball_mode.multiball.drops.paused = False
		# Add bonus info: 5000 bonus for attempting
		if 'modes_attempted' in self.bonus_base_elements:
			self.bonus_base_elements['modes_attempted'] += 5000
		else:
			self.bonus_base_elements['modes_attempted'] = 5000

		# Add bonus info: additional 10000 bonus for completing
		if successful:
			if 'modes_completed' in self.bonus_base_elements:
				self.bonus_base_elements['modes_completed'] += 10000
			else:
				self.bonus_base_elements['modes_completed'] = 10000

		# See about lighting extra ball
		if successful:
			self.num_modes_completed += 1
			if self.num_modes_completed in self.num_modes_for_extra_ball:
				self.light_extra_ball()

		# Turn on mode lamp to show it has been attempted
		self.drive_mode_lamp(self.mode, 'on')

		# See if it's time for a judge battle
		if len(self.modes_not_attempted) == 7 or len(self.modes_not_attempted) == 5 or len(self.modes_not_attempted) == 3 or len(self.modes_not_attempted) == 0:
			self.setup_judge_battle()
		# Otherwise prepare the next mode
		else:
			self.rotate_modes(1)
			self.state = 'idle'
			self.setup_next_mode()

	def judge_battle_complete(self):
		print "judges attempted"
		print self.judges_attempted
		for judge in self.judges_attempted:
			print judge
			self.game.coils['flasher' + judge].disable()
		for mode in self.modes_attempted:
			self.drive_mode_lamp(mode, 'on')
		if len(self.modes_not_attempted) > 0:
			self.rotate_modes(1)
			self.setup_next_mode()
			self.state = 'idle'
		elif self.multiball_jackpot_collected and self.crimescenes.complete():
			self.setup_ultimate_challenge()
		else:
			self.state = 'modes_completed'

	def ultimate_challenge_complete(self):
		self.reset()

class Crimescenes(Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Crimescenes, self).__init__(game, priority)
		self.level = 0
		self.mode = 'idle'
		self.targets = [1,0,0,0,0]
		self.target_award_order = [1,3,0,2,4]
		self.lamp_colors = ['W', 'R', 'Y', 'G']
		self.level_templates = [ [0,2,4], [0,2,4], 
                                         [0,2,4], [0,2,4], 
                                         [0,1,2,3,4], [0,1,2,3,4], 
                                         [0,1,2,3,4], [0,1,2,3,4], 
                                         [0,1,2,3,4], [0,1,2,3,4], 
                                         [0,1,2,3,4], [0,1,2,3,4], 
                                         [0,1,2,3,4], [0,1,2,3,4], 
                                         [0,1,2,3,4], [0,1,2,3,4] ]
		self.level_nums = [ 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5 ]
		self.bonus_num = 1
		self.extra_ball_levels = 2
		self.bonus_base_elements['crimescene_levels'] = 0

	def mode_stopped(self):
		if self.mode == 'bonus':
			self.cancel_delayed('moving_target')
		for i in range(1,6):
			for j in range(0,4):
				lampname = 'perp' + str(i) + self.lamp_colors[j]
				self.drive_mode_lamp(lampname, 'off')
		for i in range(1,5):
			lampname = 'crimeLevel' + str(i)
			self.drive_mode_lamp(lampname, 'off')

	def get_info_record(self):
		info_record = {}
		info_record['level'] = self.level
		info_record['mode'] = self.mode
		info_record['targets'] = self.targets
		return info_record

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.level = info_record['level']
			self.mode = info_record['mode']
			self.targets = info_record['targets']

		if self.mode == 'bonus':
			self.mode = 'complete'
		self.num_advance_hits = 0
		self.update_lamps()

	def update_lamps(self):
		if self.mode == 'idle':
			self.init_level(0)
		elif self.mode == 'levels':
			lampname = 'advanceCrimeLevel'
			if self.num_advance_hits == 0:
				self.drive_mode_lamp(lampname, 'on')
			elif self.num_advance_hits == 1:
				self.drive_mode_lamp(lampname, 'slow')
			elif self.num_advance_hits == 2:
				self.drive_mode_lamp(lampname, 'fast')
			else:
				self.drive_mode_lamp(lampname, 'off')
				
			for i in range(0,5):
				lampname = 'perp' + str(i+1) + self.lamp_colors[0]
				if self.targets[i]:
					self.drive_mode_lamp(lampname, 'medium')
				else:
					self.drive_mode_lamp(lampname, 'off')
			# Use 4 center crimescene lamps as a binary representation
			# of the level.
			for i in range (1,5):
				bit = 1 << (i-1)
				lampname = 'crimeLevel' + str(i)
				if (i & self.level) > 0:
					self.drive_mode_lamp(lampname, 'on')
				else:
					self.drive_mode_lamp(lampname, 'off')
		elif self.mode == 'bonus':
			for i in range(0,5):
				lampname = 'perp' + str(i+1) + self.lamp_colors[0]
				self.drive_mode_lamp(lampname, 'off')
		elif self.mode == 'complete':
			for i in range(0,5):
				if self.targets[i]:
					lampname = 'perp' + str(i+1) + self.lamp_colors[0]
					self.drive_mode_lamp(lampname, 'off')

	def sw_threeBankTargets_active(self, sw):
		if self.mode == 'levels':
			if self.num_advance_hits == 2:	
				self.award_hit()
				self.num_advance_hits = 0
				self.update_lamps()
			else:
				self.num_advance_hits += 1
				self.update_lamps()

	def sw_topRightOpto_active(self, sw):
		#See if ball came around outer left loop
		print "time"
		print self.game.switches.leftRollover.time_since_change()

		if self.game.switches.leftRollover.time_since_change() < 1:
			self.switch_hit(0)

		#See if ball came around inner left loop
		elif self.game.switches.topCenterRollover.time_since_change() < 1:
			self.switch_hit(1)

	def sw_popperR_active_for_300ms(self, sw):
		self.switch_hit(2)

	def sw_leftRollover_active(self, sw):
		#See if ball came around right loop
		if self.game.switches.topRightOpto.time_since_change() < 1:
			self.switch_hit(3)

	def sw_topCenterRollover_active(self, sw):
		#See if ball came around right loop 
		#Give it 2 seconds as ball trickles this way.  Might need to adjust.
		if self.game.switches.topRightOpto.time_since_change() < 2:
			self.switch_hit(3)

	def sw_rightRampExit_active(self, sw):
		self.switch_hit(4)

	def award_hit(self):
		for i in range(0,5):
			award_switch = self.target_award_order[i]
			if self.targets[award_switch]:
				self.switch_hit(award_switch)
				return True

	def switch_hit(self, num):
		if self.mode == 'levels':
			if self.targets[num]:
				self.game.score(1000)
			self.targets[num] = 0
			print 'self.targets'
			print self.targets
			if self.all_targets_off():
				self.level_complete()
			else:
				self.update_lamps()
		elif self.mode == 'bonus':
			if num+1 == self.bonus_num:
				self.drive_bonus_lamp(self.bonus_num, 'off')
				self.mode = 'complete'
				self.game.score(500000)
				#Play sound, lamp show, etc

	def level_complete(self):
		# Add bonus
		if 'crimescene_levels' in self.bonus_base_elements:
			self.bonus_base_elements['crimescene_levels'] += 2000
		else:
			self.bonus_base_elements['crimescene_levels'] = 2000
			
		self.game.score(10000)
		if self.level == self.extra_ball_levels:
			self.light_extra_ball_function()
		if self.level == 15:
			self.mode = 'bonus'
			self.update_lamps()
			#Play sound, lamp show, etc
			self.bonus_num = 1
			self.bonus_dir = 'up'
			self.delay(name='bonus_target', event_type=None, delay=3, handler=self.bonus_target)
			self.drive_bonus_lamp(self.bonus_num, 'on')
			for i in range(1,5):
				lampname = 'crimeLevel' + str(i)
				self.drive_mode_lamp(lampname, 'slow')
			
		else:
			self.level += 1
			self.init_level(self.level)
			#Play sound, lamp show, etc

	def bonus_target(self):
		self.drive_bonus_lamp(self.bonus_num, 'off')
		if self.bonus_num == 5:
			self.bonus_dir = 'down'

		if self.bonus_dir == 'down' and self.bonus_num == 1:
			self.mode = 'complete'
			for i in range(1,5):
				lampname = 'crimeLevel' + str(i)
				self.drive_mode_lamp(lampname, 'off')
		else:
			if self.bonus_dir == 'up':
				self.bonus_num += 1
			else:
				self.bonus_num -= 1
			self.drive_bonus_lamp(self.bonus_num, 'on')
			self.delay(name='bonus_target', event_type=None, delay=3, handler=self.bonus_target)
			

	def drive_mode_lamp(self, lamp_name, style='on'):
		if style == 'slow':
			self.game.lamps[lamp_name].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		if style == 'medium':
			self.game.lamps[lamp_name].schedule(schedule=0x0f0f0f0f, cycle_seconds=0, now=True)
		if style == 'fast':
			self.game.lamps[lamp_name].schedule(schedule=0x55555555, cycle_seconds=0, now=True)
		elif style == 'on':
			self.game.lamps[lamp_name].pulse(0)
		elif style == 'off':
			self.game.lamps[lamp_name].disable()

	def drive_bonus_lamp(self, lamp_num, style='on'):
		for i in range(1,len(self.lamp_colors)):
			lamp_name = 'perp' + str(lamp_num) + self.lamp_colors[i]
			if style == 'slow':
				self.game.lamps[lamp_name].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
			elif style == 'on':
				self.game.lamps[lamp_name].pulse(0)
			elif style == 'off':
				self.game.lamps[lamp_name].disable()
		

	def all_targets_off(self):
		for i in range(0,5):
			if self.targets[i]:
				return False
		return True

	def init_level(self, level):
		self.mode = 'levels'
		level_template = self.level_templates[level]
		print "level template"
		print level_template
		shuffle(level_template)
		print "shuffled_level template"
		print level_template
		# First initialize targets (redundant?)
		for i in range(0,5):
			self.targets[i] = 0
		# Now fill targets according to shuffled template
		for i in range(0,5):
			print "len(self.level_templates[level])"
			print len(self.level_templates[level])
			print self.level_nums
			if i < self.level_nums[level] and i < len(self.level_templates[level]):
				self.targets[level_template[i]] = 1
		print "targets"
		print self.targets
		self.update_lamps()

	def complete(self):
		return self.mode == 'complete'

class ChainFeature(Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ChainFeature, self).__init__(game, priority)
		self.completed = False

	def register_callback_function(self, function):
		self.callback = function


class Pursuit(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Pursuit, self).__init__(game, priority)

	def mode_started(self):
		self.game.coils.flasherPursuitL.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.game.coils.flasherPursuitR.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots = 0

	def mode_stopped(self):
		self.game.coils.flasherPursuitL.disable()
		self.game.coils.flasherPursuitR.disable()

	def sw_leftRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == 5:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()
	
class Blackout(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Blackout, self).__init__(game, priority)

	def mode_started(self):
		self.game.lamps.gi01.disable()
		self.game.lamps.gi02.disable()
		self.game.lamps.gi03.disable()
		self.game.lamps.blackoutJackpot.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots = 0

	def mode_stopped(self):
		self.game.lamps.blackoutJackpot.disable()
		self.game.coils.flasherBlackout.disable()
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.pulse(0)
		self.game.lamps.gi03.pulse(0)

	def sw_centerRampExit_active(self, sw):
		self.completed = True
		self.game.coils.flasherBlackout.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == 2:
			self.completed = True
			self.game.set_status('Great job!')
			self.game.score(50000)

class Sniper(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Sniper, self).__init__(game, priority)

	def mode_started(self):
		self.game.lamps.awardSniper.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0

	def mode_stopped(self):
		self.game.lamps.awardSniper.disable()

	def sw_popperR_active_for_300ms(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == 2:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()

class BattleTank(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(BattleTank, self).__init__(game, priority)

	def mode_started(self):
		self.game.lamps.tankCenter.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.game.lamps.tankLeft.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.game.lamps.tankRight.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = {'left':False,'center':False,'right':False}

	def mode_stopped(self):
		self.game.lamps.tankCenter.disable()
		self.game.lamps.tankLeft.disable()
		self.game.lamps.tankRight.disable()

	def sw_topRightOpto_active(self, sw):
		if not self.shots['left']:
			if self.game.switches.leftRollover.time_since_change() < 1:
				self.game.lamps.tankLeft.disable()
				self.shots['left'] = True
				self.check_for_completion()
				self.game.score(10000)

	def sw_centerRampExit_active(self, sw):
		if not self.shots['center']:
			self.game.lamps.tankCenter.disable()
			self.shots['center'] = True
			self.check_for_completion()
			self.game.score(10000)

	def sw_threeBankTargets_active(self, sw):
		if not self.shots['right']:
			self.game.lamps.tankRight.disable()
			self.shots['right'] = True
			self.check_for_completion()
			self.game.score(10000)

	def check_for_completion(self):
		if self.shots['right'] and self.shots['left'] and self.shots['center']:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()

class Meltdown(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Meltdown, self).__init__(game, priority)

	def mode_started(self):
		self.game.lamps.stopMeltdown.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0

	def mode_stopped(self):
		self.game.lamps.stopMeltdown.disable()

	def sw_captiveBall1_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def sw_captiveBall2_active(self, sw):
		self.shots += 2
		self.check_for_completion()
		self.game.score(10000)

	def sw_captiveBall2_active(self, sw):
		self.shots += 3
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots >= 3:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()

class Impersonator(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Impersonator, self).__init__(game, priority)

	def mode_started(self):
		self.game.lamps.awardBadImpersonator.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0
		self.timer = 0
		self.delay(name='moving_target', event_type=None, delay=1, handler=self.moving_target)
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active(): 
			self.game.coils.resetDropTarget.pulse(40)

	def mode_stopped(self):
		self.game.lamps.awardBadImpersonator.disable()
		self.game.lamps.dropTargetJ.disable()
		self.game.lamps.dropTargetU.disable()
		self.game.lamps.dropTargetD.disable()
		self.game.lamps.dropTargetG.disable()
		self.game.lamps.dropTargetE.disable()
		self.cancel_delayed('moving_target')

	def check_for_completion(self):
		if self.shots == 5:
			self.completed = True
			self.game.set_status('Great Job!')
			self.game.score(50000)

	def sw_dropTargetJ_active(self,sw):
		if self.timer%6 == 0:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def sw_dropTargetU_active(self,sw):
		if self.timer%6 == 0 or self.timer%6 == 1 or self.timer%6 == 5:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def sw_dropTargetD_active(self,sw):
		if self.timer%6 == 2 or self.timer%6 == 4 or self.timer%6 == 1 or self.timer%6 == 5:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def sw_dropTargetG_active(self,sw):
		if self.timer%6 == 2 or self.timer%6 == 3 or self.timer%6 == 4:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def sw_dropTargetE_active(self,sw):
		if self.timer%6 == 3:
			self.shots += 1
			self.game.score(10000)
		self.game.coils.resetDropTarget.pulse(40)
		self.check_for_completion()

	def moving_target(self):
		self.timer += 1
		self.game.lamps.dropTargetJ.disable()
		self.game.lamps.dropTargetU.disable()
		self.game.lamps.dropTargetD.disable()
		self.game.lamps.dropTargetG.disable()
		self.game.lamps.dropTargetE.disable()
		if self.timer%6 == 0:
			self.game.lamps.dropTargetJ.pulse(0)
			self.game.lamps.dropTargetU.pulse(0)
		elif self.timer%6 == 1 or self.timer%6==5:
			self.game.lamps.dropTargetU.pulse(0)
			self.game.lamps.dropTargetD.pulse(0)
		elif self.timer%6 == 2 or self.timer%6==4:
			self.game.lamps.dropTargetD.pulse(0)
			self.game.lamps.dropTargetG.pulse(0)
		elif self.timer%6 == 3:
			self.game.lamps.dropTargetG.pulse(0)
			self.game.lamps.dropTargetE.pulse(0)
		self.delay(name='moving_target', event_type=None, delay=1, handler=self.moving_target)
		

class Safecracker(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Safecracker, self).__init__(game, priority)

	def mode_started(self):
		self.game.lamps.awardSafecracker.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.shots = 0
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active():
			self.game.coils.resetDropTarget.pulse(40)
		self.delay(name='trip_target', event_type=None, delay=2, handler=self.trip_target)

	def mode_stopped(self):
		self.game.lamps.awardSafecracker.disable()
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active():
			self.game.coils.resetDropTarget.pulse(40)

	def sw_subwayEnter2_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == 3:
			self.completed = True
			self.game.set_status('Mode completed!')
			self.game.score(50000)
			self.callback()

	def trip_target(self):
		self.game.coils.tripDropTarget.pulse(50)


class ManhuntMillions(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ManhuntMillions, self).__init__(game, priority)

	def mode_started(self):
		self.game.coils.flasherPursuitL.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots = 0

	def mode_stopped(self):
		self.game.coils.flasherPursuitL.disable()

	def sw_leftRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == 5:
			self.completed = True
			self.game.set_status('Great Job!')
			self.game.score(50000)
			self.callback()

class Stakeout(ChainFeature):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(Stakeout, self).__init__(game, priority)

	def mode_started(self):
		self.game.coils.flasherPursuitR.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)
		self.shots = 0

	def mode_stopped(self):
		self.game.coils.flasherPursuitR.disable()

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()
		self.game.score(10000)

	def check_for_completion(self):
		if self.shots == 3:
			self.completed = True
			self.game.set_status('Great Job!')
			self.game.score(50000)

	
class ModeTimer(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ModeTimer, self).__init__(game, priority)
		self.timer = 0;

	def mode_stopped(self):
		self.timer = 0;

	def start(self, time):
		self.timer = time
		self.delay(name='intro', event_type=None, delay=1, handler=self.decrement_timer)
	def stop(self):
		self.timer = 0

	def add(self,adder):
		self.timer += adder 

	def decrement_timer(self):
		if self.timer > 0:
			self.timer -= 1
			self.delay(name='intro', event_type=None, delay=1, handler=self.decrement_timer)
			self.game.set_status('Mode Timer: ' + str(self.timer))
		else:
			self.callback()

	
class PlayIntro(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, mode, exit_function, exit_function_param, font):
		super(PlayIntro, self).__init__(game, priority)
		self.abort = 0
		self.exit_function = exit_function
		self.exit_function_param = exit_function_param
		self.banner_layer = dmd.TextLayer(128/2, 7, font, "center")
		self.countdown_layer = dmd.TextLayer(128/2, 20, font, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer, self.countdown_layer])
		self.mode = mode
	
	def mode_started(self):
		self.frame_counter = 5
		self.delay(name='intro', event_type=None, delay=1, handler=self.next_frame)
		self.banner_layer.set_text(str(self.mode) + ' intro')
		self.game.dmd.layers.append(self.layer)

	def mode_stopped(self):
		if self.abort:
			self.cancel_delayed('intro')

	def sw_flipperLwL_active(self, sw):
		if self.game.switches.flipperLwR.is_active():
			self.game.dmd.layers.remove(self.layer)
			self.exit_function(self.exit_function_param)	
			self.abort = 1

	def sw_flipperLwR_active(self, sw):
		if self.game.switches.flipperLwL.is_active():
			self.game.dmd.layers.remove(self.layer)
			self.exit_function(self.exit_function_param)	
			self.abort = 1

	def next_frame(self):
		if self.frame_counter > 0:
			self.delay(name='intro', event_type=None, delay=1, handler=self.next_frame)
			self.countdown_layer.set_text(str(self.frame_counter))
			self.frame_counter -= 1
		else:
			self.game.dmd.layers.remove(self.layer)
			self.exit_function(self.exit_function_param)	


class Multiball(Scoring_Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, deadworld_mod_installed, font):
		super(Multiball, self).__init__(game, priority)
		self.deadworld_mod_installed = deadworld_mod_installed
		self.lock_enabled = 0
		self.num_balls_locked = 0
		self.num_balls_to_eject = 0
		self.virtual_locks_needed = 0
		self.banner_layer = dmd.TextLayer(128/2, 7, font, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
		self.state = 'load'
		self.displaying_text = 0
		self.enable_ball_save_after_launch=False
		self.paused = 0
		self.num_locks_lit = 0
		self.targets = {'J':'up', 'U':'up', 'D':'up', 'G':'up', 'E':'up'}
		self.num_times_played = 0
		self.num_left_ramp_shots_hit = 0
		self.num_left_ramp_shots_needed = 1
		self.jackpot_lit = False
		self.drops = procgame.modes.BasicDropTargetBank(self.game, priority=priority+1, prefix='dropTarget', letters='JUDGE')
	
	def mode_started(self):
		self.game.coils.globeMotor.disable()
		self.lock_lamps()
		self.game.deadworld.initialize()
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, False)
		for target in self.targets:
			self.targets[target] = 'up'
			self.game.lamps['dropTarget' + target].pulse(0)
		self.drops.on_advance = self.on_drops_advance
		self.drops.on_completed = self.possibly_light_lock
		self.drops.auto_reset = True
		self.game.modes.add(self.drops)

	def mode_stopped(self):
		self.game.coils.flasherGlobe.disable()
		self.game.lamps.gi04.disable()
		self.game.modes.remove(self.drops)
		#if self.displaying_text:
		#	self.game.dmd.layers.remove(self.layer)
		#	self.cancel_delayed(['remove_dmd_layer'])

	def on_drops_advance(self, mode):
		pass

	def is_active(self):
		return self.state == 'multiball'

	def end_multiball(self):
		self.state = 'load'
		self.game.set_status(self.state)
		self.game.lamps.gi04.disable()
		self.end_callback()
		self.jackpot_lit = False
		self.game.lamps.multiballJackpot.disable()
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active(): 
			self.game.coils.resetDropTarget.pulse(40)
		self.num_locks_lit = 0
		self.lock_lamps()

	def start_multiball(self):
		self.num_balls_locked = 0
		self.state = 'multiball'
		self.game.lamps.gi04.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
		self.display_text("Multiball!")
		self.start_callback()
		self.num_left_ramp_shots_hit = 0
		self.num_left_ramp_shots_needed = 1
		self.jackpot_lit = False
		self.lock_lamps()

	def jackpot(self):
		self.game.score(100000)
		self.lock_lamps()
		self.jackpot_callback()

	def sw_subwayEnter2_active(self,sw):
		if self.jackpot_lit:
			self.display_text("Jackpot!")
			self.jackpot_lit = False
			self.delay(name='jackpot', event_type=None, delay=1.5, handler=self.jackpot)
			self.game.lamps.multiballJackpot.disable()
			self.num_left_ramp_shots_hit = 0

	def display_text(self, text):
		# use a varable to protect against adding the layer twice
		#if self.displaying_text:
		#	self.game.dmd.layers.remove(self.layer)
		#	self.cancel_delayed(['remove_dmd_layer'])
		#self.displaying_text = 1
		self.banner_layer.set_text(text,3)
		self.game.dmd.layers.append(self.layer)
		self.delay(name='remove_dmd_layer', event_type=None, delay=2.5, handler=self.remove_dmd_layer)

	def remove_dmd_layer(self):
		self.game.dmd.layers.remove(self.layer)
		self.displaying_text = 0

	def update_info_record(self, info_record):
		if len(info_record) > 0:
			self.state = info_record['state']
			self.num_balls_locked = info_record['num_balls_locked']
			self.num_locks_lit = info_record['num_locks_lit']
			self.num_times_played = info_record['num_times_played']

		# Virtual locks are needed when there are more balls physically locked 
		# than the player has locked through play.  This happens when
		# another player locks more balls than the current player.  Use
		# Virtual locks > 0 for this case.
		# Use Virtual locks < 0 when the player has locked more balls than are
		# physically locked.  This could happen when another player plays
		# multiball and empties the locked balls.
		if self.deadworld_mod_installed:
			self.virtual_locks_needed = self.game.deadworld.num_balls_locked - self.num_balls_locked
		else:
			self.virtual_locks_needed = 0

		if self.virtual_locks_needed < 0:
			# enable the lock so the player can quickly re-lock
			self.enable_lock()
			self.display_text("Lock is Lit!")
			self.num_balls_locked = self.game.deadworld.num_balls_locked
			self.num_locks_lit = 0 - self.virtual_locks_needed
		elif self.num_balls_locked < self.num_locks_lit:
			self.enable_lock()
			self.display_text("Lock is Lit!")
			
		self.lock_lamps()

	def get_info_record(self):
		info_record = {}
		info_record['state'] = self.state
		info_record['num_balls_locked'] = self.num_balls_locked
		info_record['num_locks_lit'] = self.num_locks_lit
		info_record['num_times_played'] = self.num_times_played
		return info_record

	def pause(self):
		self.paused = 1
		if self.lock_enabled:
			self.disable_lock()

	def resume(self):
		self.paused = 0
		if self.lock_enabled:
			self.enable_lock()

	def disable_lock(self):
		self.game.deadworld.disable_lock()
		self.lock_enabled = 0
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, False)

	def enable_lock(self):
		self.game.deadworld.enable_lock()
		self.game.coils.flasherGlobe.schedule(schedule=0x0000AAAA, cycle_seconds=2, now=True)
		self.lock_enabled = 1
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, True)
		

	def sw_leftRampToLock_active(self, sw):
		if self.lock_enabled:
			self.game.coils.flasherGlobe.schedule(schedule=0xAAAAAAAA, cycle_seconds=2, now=True)
			self.num_balls_locked += 1
			self.display_text("Ball " + str(self.num_balls_locked) + " Locked!")
			if self.num_balls_locked == 3:
				self.disable_lock()
				if self.deadworld_mod_installed:
					self.game.deadworld.eject_balls(3)
					self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=4, time=25, now=False, allow_multiple_saves=True)
					self.launch_ball(1)
				else:
					self.launch_ball(3)
					self.enable_ball_save_after_launch=True
					self.delay(name='stop_globe', event_type=None, delay=7.0, handler=self.stop_globe)
				self.start_multiball()
			elif self.num_balls_locked == self.num_locks_lit:
				self.disable_lock()
				if self.deadworld_mod_installed:
					self.launch_ball(1)
				
			# When not yet multiball, launch a new ball each time
			# one is locked.
			elif self.deadworld_mod_installed:
				self.launch_ball(1)

		else:
			if self.deadworld_mod_installed:
				self.game.deadworld.eject_balls(1)
		self.lock_lamps()

	def possibly_light_lock(self, mode):
		if self.state == 'load' and not self.paused:
			# Prepare to lock
			if self.num_locks_lit < 3:
				for target in self.targets:
					self.targets[target] = 'up'
					self.game.lamps['dropTarget' + target].pulse(0)
					
				self.num_locks_lit += 1
				# Don't enable locks if doing virtual locks.
				if self.virtual_locks_needed == 0:
					self.enable_lock()
					self.display_text("Lock is Lit!")

			self.lock_lamps()

	def sw_leftRampExit_active(self,sw):
		if self.state == 'load':
			if self.virtual_locks_needed > 0:
				self.num_balls_locked += 1
				self.virtual_locks_needed -= 1

			self.lock_lamps()
		elif self.state == 'multiball':
			if not self.jackpot_lit:
				self.num_left_ramp_shots_hit += 1
				if self.num_left_ramp_shots_hit == self.num_left_ramp_shots_needed:
					self.jackpot_lit = True
					self.game.lamps.multiballJackpot.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
				if self.game.switches.dropTargetD.is_inactive():
					self.game.coils.tripDropTarget.pulse(50)
				self.lock_lamps()

	def lock_lamps(self):
		if self.state == 'load':
			for i in range(1,4):
				lampname = 'lock' + str(i)
				if self.num_locks_lit >= i and not self.paused:
					if self.num_balls_locked >= i:
						self.game.lamps[lampname].pulse(0)
					elif self.num_balls_locked < i:
						self.game.lamps[lampname].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
					else:
						self.game.lamps[lampname].disable()
				else:
					self.game.lamps[lampname].disable()
	
		elif self.state == 'multiball' and not self.jackpot_lit:
			self.game.lamps.lock1.schedule(schedule=0x000f000f, cycle_seconds=0, now=False)
			self.game.lamps.lock2.schedule(schedule=0x003c003c, cycle_seconds=0, now=False)
			self.game.lamps.lock3.schedule(schedule=0x00f000f0, cycle_seconds=0, now=False)
			
		else:
			self.game.lamps.lock1.disable()
			self.game.lamps.lock2.disable()
			self.game.lamps.lock3.disable()
	

	def launch_ball(self, num):
		print "Launching Ball"
		self.game.coils.trough.pulse(40)
		num -= 1
		if num > 0:
			self.delay(name='launch', event_type=None, delay=2.0, handler=self.launch_ball, param=num)
		else:
			if self.enable_ball_save_after_launch:
				self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=4, time=25, now=False, allow_multiple_saves=True)
				self.enable_ball_save_after_launch = False
			

	def how_many_balls_locked(self):
		return self.num_balls_locked

	def stop_globe(self):
		self.game.deadworld.mode_stopped()
		
