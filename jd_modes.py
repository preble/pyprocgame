from procgame import *

class JD_Modes(game.Mode):
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

	def reset(self):
		self.state = 'idle'
		self.judges_attempted = []
		self.judges_not_attempted = ['Fire', 'Fear', 'Death', 'Mortis']
		self.modes_attempted = []
		self.modes_not_attempted = ['pursuit', 'blackout', 'sniper', 'battleTank', 'impersonator', 'meltdown', 'safecracker', 'manhunt', 'stakeout']
		self.modes_just_attempted = []
		self.active_mode_pointer = 0
		self.multiball_active = False
		self.multiball_jackpot_collected = False
		self.modes_not_attempted_ptr = 0
		self.mode_active = False
		self.crimescenes = 0
		self.mode_list = {}
		self.mode = 0
		self.two_ball_active = False
		for mode in self.modes_not_attempted:
			self.drive_mode_lamp(mode, 'off')
		for judge in self.judges_not_attempted:
			self.game.coils['flasher' + judge].disable()
		if self.game.switches.dropTargetJ.is_active() or self.game.switches.dropTargetU.is_active() or self.game.switches.dropTargetD.is_active() or self.game.switches.dropTargetG.is_active() or self.game.switches.dropTargetE.is_active(): 
			self.game.coils.resetDropTarget.pulse(40)

	def mode_started(self):
		self.mode_timer.register_callback_function(self.mode_over)
		self.mode_pursuit.register_callback_function(self.mode_over)
		self.mode_list['pursuit'] = self.mode_pursuit
		self.mode_blackout.register_callback_function(self.mode_over)
		self.mode_list['blackout'] = self.mode_blackout
		self.mode_sniper.register_callback_function(self.mode_over)
		self.mode_list['sniper'] = self.mode_sniper
		self.mode_battleTank.register_callback_function(self.mode_over)
		self.mode_list['battleTank'] = self.mode_battleTank
		self.mode_impersonator.register_callback_function(self.mode_over)
		self.mode_list['impersonator'] = self.mode_impersonator
		self.mode_meltdown.register_callback_function(self.mode_over)
		self.mode_list['meltdown'] = self.mode_meltdown
		self.mode_safecracker.register_callback_function(self.mode_over)
		self.mode_list['safecracker'] = self.mode_safecracker
		self.mode_manhunt.register_callback_function(self.mode_over)
		self.mode_list['manhunt'] = self.mode_manhunt
		self.mode_stakeout.register_callback_function(self.mode_over)
		self.mode_list['stakeout'] = self.mode_stakeout
		self.game.modes.add(self.mode_timer)

	def mode_stopped(self):
		self.game.modes.remove(self.mode_timer)
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
		info_record['crimescenes'] = self.crimescenes
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
			self.crimescenes = info_record['crimescenes']
			print "modes attempted"
			print self.modes_attempted
		
		self.begin_processing()

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


	def rotate_modes(self, adder):
		self.disable_not_attempted_mode_lamps()
		self.active_mode_pointer += adder
		self.modes_not_attempted_ptr = self.active_mode_pointer % len(self.modes_not_attempted)
		print "mode_ptr"
		print self.modes_not_attempted_ptr
		if not self.mode_active:
			self.drive_mode_lamp(self.modes_not_attempted[self.modes_not_attempted_ptr],'ready')

	def disable_not_attempted_mode_lamps(self):
		for mode in self.modes_not_attempted:
			self.game.lamps[mode].disable()

	def drive_mode_lamp(self, lamp_name, style='on'):
		if style == 'ready':
			self.game.lamps[lamp_name].schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)
		elif style == 'on':
			self.game.lamps[lamp_name].pulse(0)
		elif style == 'off':
			self.game.lamps[lamp_name].disable()

	def sw_fireR_active(self, sw):
		if not self.multiball_active and self.state == 'idle':
			self.game.set_status("hi")
			self.rotate_modes(1)
		else:
			print "hello"
			print self.state
			print self.multiball_active
			self.game.set_status("hello")

	def sw_fireL_active(self, sw):
		if not self.multiball_active and self.state == 'idle':
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

	def register_helper_functions(self, helper_functions):
		self.popperR_launch = helper_functions['popperR_launch']
		self.main_launch = helper_functions['main_launch']

	def activate_mode(self, mode):
		self.game.modes.remove(self.play_intro)
		self.popperR_launch()
		
		if self.state == 'idle':
			self.game.lamps[self.modes_not_attempted[self.modes_not_attempted_ptr]].schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
			self.mode = self.modes_not_attempted[self.modes_not_attempted_ptr]
			print "self.mode"
			print self.mode
			self.modes_not_attempted.remove(self.mode)
			self.modes_attempted.append(self.mode)
			self.modes_just_attempted.append(self.mode)
			self.state = 'mode'
			self.game.modes.add(self.mode_list[self.mode])
			self.mode_timer.start(5)
			self.mode_active = True
		elif self.state == 'pre_judge_battle':
                        # Start modes from self.modes_just_attempted
			judge = self.judges_not_attempted[0]
			self.judges_not_attempted.remove(judge)
			self.judges_attempted.append(judge)
			self.game.set_status('battle in progress')
			self.state = 'judge_battle'
			for mode in self.modes_attempted:
				self.drive_mode_lamp(mode, 'off')
			for mode in self.modes_just_attempted:
				self.drive_mode_lamp(mode, 'ready')
			self.modes_just_attempted = []
			# Start 2-ball multiball
			self.main_launch()
			self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=2, time=10, now=False, allow_multiple_saves=True)
			self.two_ball_active = True
			
			
		elif self.state == 'pre_ultimate_challenge':
			self.game.set_status('challenge in progress')
			self.state = 'ultimate_challenge'

	def setup_next_mode(self):
		if not self.multiball_active:
			self.drive_mode_lamp(self.modes_not_attempted[self.modes_not_attempted_ptr],'ready')
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def setup_judge_battle(self):
		self.state = 'pre_judge_battle'
		if not self.multiball_active:
			self.game.coils['flasher' + self.judges_not_attempted[0]].schedule(schedule=0x00000003, cycle_seconds=0, now=True)
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def setup_ultimate_challenge(self):
		self.state = 'pre_ultimate_challenge'
		if not self.multiball_active:
			self.game.lamps.rightStartFeature.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

	def multiball_started(self):
		self.game.lamps.rightStartFeature.disable()
		self.multiball_active = True

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
		self.drive_mode_lamp(self.mode, 'on')
		if len(self.modes_not_attempted) == 7 or len(self.modes_not_attempted) == 5 or len(self.modes_not_attempted) == 3 or len(self.modes_not_attempted) == 0:
			self.setup_judge_battle()
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
		elif self.multiball_jackpot_collected and self.crimescenes >= self.crimescenes_required:
			self.setup_ultimate_challenge()
		else:
			self.state = 'modes_completed'

	def ultimate_challenge_complete(self):
		self.reset()

class ChainFeature(game.Mode):
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

	def sw_rightRampExit_active(self, sw):
		self.shots += 1
		self.check_for_completion()

	def check_for_completion(self):
		if self.shots == 5:
			self.completed = True
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

	def mode_stopped(self):
		self.game.lamps.blackoutJackpot.disable()
		self.game.coils.flasherBlackout.disable()
		self.game.lamps.gi01.pulse(0)
		self.game.lamps.gi02.pulse(0)
		self.game.lamps.gi03.pulse(0)

	def sw_centerRampExit_active(self, sw):
		self.completed = True
		self.game.coils.flasherBlackout.schedule(schedule=0x000F000F, cycle_seconds=0, now=True)

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

	def check_for_completion(self):
		if self.shots == 2:
			self.completed = True
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
		switch_order = ['leftRollover', 'topRightOpto']
		if not self.shots['left']:
			if self.game.did_switches_hit_in_order(switch_order,0.500):
				self.game.lamps.tankLeft.disable()
				self.shots['left'] = True
				self.check_for_completion()

	def sw_topCenterRollover_active(self, sw):
		switch_order = ['leftRollover', 'topCenterRollover']
		if not self.shots['left']:
			#if self.game.did_switches_hit_in_order(switch_order,0.500):
			self.game.lamps.tankLeft.disable()
			self.shots['left'] = True
			self.check_for_completion()

	def sw_centerRampExit_active(self, sw):
		if not self.shots['center']:
			self.game.lamps.tankCenter.disable()
			self.shots['center'] = True
			self.check_for_completion()

	def sw_threeBankTargets_active(self, sw):
		if not self.shots['right']:
			self.game.lamps.tankRight.disable()
			self.shots['right'] = True
			self.check_for_completion()

	def check_for_completion(self):
		if self.shots['right'] and self.shots['left'] and self.shots['center']:
			self.completed = True
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

	def sw_captiveBall2_active(self, sw):
		self.shots += 2
		self.check_for_completion()

	def sw_captiveBall2_active(self, sw):
		self.shots += 3
		self.check_for_completion()

	def check_for_completion(self):
		if self.shots >= 3:
			self.completed = True
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

	def sw_subwayEnter2(self, sw):
		self.shots += 1
		self.check_for_completion()

	def check_for_completion(self):
		if self.shots == 3:
			self.completed = True
			self.callback()

	def sw_dropTargetJ_active(self,sw):
		if self.timer%6 == 0:
			self.shots += 1
		self.game.coils.resetDropTarget.pulse(40)

	def sw_dropTargetU_active(self,sw):
		if self.timer%6 == 0 or self.timer%6 == 1 or self.timer%6 == 5:
			self.shots += 1
		self.game.coils.resetDropTarget.pulse(40)

	def sw_dropTargetD_active(self,sw):
		if self.timer%6 == 2 or self.timer%6 == 4 or self.timer%6 == 1 or self.timer%6 == 5:
			self.shots += 1
		self.game.coils.resetDropTarget.pulse(40)

	def sw_dropTargetG_active(self,sw):
		if self.timer%6 == 2 or self.timer%6 == 3 or self.timer%6 == 4:
			self.shots += 1
		self.game.coils.resetDropTarget.pulse(40)

	def sw_dropTargetE_active(self,sw):
		if self.timer%6 == 3:
			self.shots += 1
		self.game.coils.resetDropTarget.pulse(40)

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

	def check_for_completion(self):
		if self.shots == 3:
			self.completed = True
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

	def check_for_completion(self):
		if self.shots == 3:
			self.completed = True
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

	def check_for_completion(self):
		if self.shots == 3:
			self.completed = True
			self.callback()

	
class ModeTimer(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority):
		super(ModeTimer, self).__init__(game, priority)
		self.timer = 0;

	def mode_stopped(self):
		self.timer = 0;

	def register_callback_function(self, function):
		self.callback = function
	
	def start(self, time):
		self.timer = time
		self.delay(name='intro', event_type=None, delay=1, handler=self.decrement_timer)
	def stop(self):
		self.timer = 0

	def decrement_timer(self):
		if self.timer > 0:
			self.timer -= 1
			self.delay(name='intro', event_type=None, delay=1, handler=self.decrement_timer)
			self.game.set_status('Mode Timer: ' + str(self.timer))
		else:
			self.callback()
			self.game.set_status('Mode Timer Expired')

	
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


class Multiball(game.Mode):
	"""docstring for AttractMode"""
	def __init__(self, game, priority, deadworld_mod_installed, font):
		super(Multiball, self).__init__(game, priority)
		self.deadworld_mod_installed = deadworld_mod_installed
		self.lock_enabled = 0
		self.num_balls_locked = 0
		self.num_balls_to_eject = 0
		self.num_left_ramp_shots = 0
		self.virtual_locks_needed = 0
		self.banner_layer = dmd.TextLayer(128/2, 7, font, "center")
		self.layer = dmd.GroupedLayer(128, 32, [self.banner_layer])
		self.state = 'load'
		self.displaying_text = 0
		self.enable_ball_save_after_launch=False
	
	def mode_started(self):
		self.game.coils.globeMotor.disable()
		self.lock_lamps()
		self.game.deadworld.initialize()
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, False)

	def mode_stopped(self):
		self.game.coils.flasherGlobe.disable()
		self.game.lamps.gi04.disable()
		#if self.displaying_text:
		#	self.game.dmd.layers.remove(self.layer)
		#	self.cancel_delayed(['remove_dmd_layer'])

	def is_active(self):
		return self.state == 'multiball'

	def end_multiball(self):
		self.state = 'multiball_complete'
		self.game.set_status(self.state)
		self.game.lamps.gi04.disable()

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
			self.state = info_record[0]
			self.num_balls_locked = info_record[1]

		# Virtual locks are needed when there are more balls physically locked 
		# than the player has locked through play.  This happens when
		# another player locks more balls than the current player.  Use
		# Virtual locks > 0 for this case.
		# Use Virtual locks < 0 when the player has locked more balls than are
		# physically locked.  This could happen when another player plays
		# multiball and empties the locked balls.
		if self.deadworld_mod_installed:
			self.virtual_locks_needed = self.game.deadworld.num_balls_locked - self.num_balls_locked

		if self.virtual_locks_needed < 0:
			# enable the lock the player can quickly re-lock
			self.enable_lock()
			self.num_balls_locked = self.game.deadworld.num_balls_locked
			# pre-set the ramp shots to get the lock light blinking appropriately
			self.num_left_ramp_shots = 3
		self.lock_lamps()

	def get_info_record(self):
		info_record = [self.state, self.num_balls_locked]
		return info_record

	def disable_lock(self):
		self.game.deadworld.disable_lock()
		self.lock_enabled = 0
		switch_num = self.game.switches['leftRampEnter'].number
		self.game.install_switch_rule_coil_pulse(switch_num, 'closed_debounced', 'diverter', 255, True, False)

	def enable_lock(self):
		self.display_text("Lock is Lit!")
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
			# Player needs to re-fill the locks
			if self.virtual_locks_needed < 0:
				# Increment back towards 0
				self.virtual_locks_needed += 1
				# Launch a new ball since the current one is locked.
				self.launch_ball(1)
				# See if finished re-locking
				if self.virtual_locks_needed == 0:
					self.disable_lock()
			else:	
				# Start multiball with the 4th lock
				if self.num_balls_locked == 4:
					if self.deadworld_mod_installed:
						self.game.deadworld.eject_balls(4)
						self.game.start_of_ball_mode.ball_save.start(num_balls_to_save=4, time=25, now=True, allow_multiple_saves=True)
					else:
						self.launch_ball(3)
						self.enable_ball_save_after_launch=True
						self.delay(name='stop_globe', event_type=None, delay=7.0, handler=self.stop_globe)
					self.num_balls_locked = 0
					self.state = 'multiball'
					self.game.lamps.gi04.schedule(schedule=0x00FF00FF, cycle_seconds=0, now=True)
					self.display_text("Multiball!")
				# When not yet multiball, launch a new ball each time
				# one is locked.
				elif self.deadworld_mod_installed:
					self.launch_ball(1)
				self.disable_lock()	
				# Reset the ramp count
				self.num_left_ramp_shots = 0
		else:
			if self.deadworld_mod_installed:
				self.game.deadworld.eject_balls(1)
		self.lock_lamps()

	def sw_leftRampExit_active(self,sw):
		#ignore slow moving balls that made it by the diverter
		if self.state == 'load':
			if not self.lock_enabled:
				# Prepare to lock
				if self.num_left_ramp_shots == 200:
					# Don't enable locks if doing virtual locks.
					if self.virtual_locks_needed == 0:
						self.enable_lock()
					self.num_left_ramp_shots += 1

				# Should only get here if doing virtual locks,
				# but check anyway.
				elif self.num_left_ramp_shots == 3:
					if self.virtual_locks_needed > 0:
						self.num_balls_locked += 1
						self.virtual_locks_needed -= 1
						self.num_left_ramp_shots = 0
				else:
					self.num_left_ramp_shots += 1

			self.lock_lamps()

	def lock_lamps(self):
		if self.state == 'load':
			if self.num_left_ramp_shots == 0:
				schedule = 0x0000ffff
			elif self.num_left_ramp_shots == 1:
				schedule = 0x00ff00ff
			elif self.num_left_ramp_shots == 2:
				schedule = 0xf0f0f0f0
			else:
				schedule = 0xaaaaaaaa
			if self.num_balls_locked == 0:
				self.game.lamps.lock1.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock2.disable()
				self.game.lamps.lock3.disable()
			elif self.num_balls_locked == 1:
				self.game.lamps.lock1.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock3.disable()
			elif self.num_balls_locked == 2:
				self.game.lamps.lock1.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=0xffffffff, cycle_seconds=0, now=True)
				self.game.lamps.lock3.schedule(schedule=schedule, cycle_seconds=0, now=True)
			elif self.num_balls_locked == 3:
				self.game.lamps.lock1.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock2.schedule(schedule=schedule, cycle_seconds=0, now=True)
				self.game.lamps.lock3.schedule(schedule=schedule, cycle_seconds=0, now=True)
		else:
			self.game.lamps.lock1.disable()
			self.game.lamps.lock2.disable()
			self.game.lamps.lock3.disable()

	def launch_ball(self, num):
		print "Launching Ball"
		self.game.coils.trough.pulse(20)
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
		
