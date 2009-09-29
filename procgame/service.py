from game import *
from dmd import *

class ServiceModeSkeleton(Mode):
	"""Service Mode List base class."""
	def __init__(self, game, priority, font):
		super(ServiceModeSkeleton, self).__init__(game, priority)
		self.name = ""
		self.title_layer = TextLayer(1, 1, font, "left")
		self.item_layer = TextLayer(128/2, 12, font, "center")
		self.instruction_layer = TextLayer(1, 25, font, "left")
		self.layer = GroupedLayer(128, 32, [self.title_layer, self.item_layer, self.instruction_layer])
		self.no_exit_switch = game.machineType == 'sternWhitestar'
		if self.no_exit_switch:
			self.add_switch_handler(name='down', event_type='closed', delay=None, handler=self.shift_exit)
		else:
			self.add_switch_handler(name='exit', event_type='closed', delay=None, handler=self.exit)

	def mode_started(self):
		self.title_layer.set_text(str(self.name))
		self.game.sound.play('service_enter')
		self.game.dmd.layers.append(self.layer)

	def mode_stopped(self):
		self.game.sound.play('service_exit')
		self.game.dmd.layers.remove(self.layer)

	def disable(self):
		pass

	def shift_exit(self, sw):
		if self.game.switches.enter.is_closed():
			self.game.modes.remove(self)
			return True

	def exit(self, sw):
		self.game.modes.remove(self)
		return True

class ServiceModeList(ServiceModeSkeleton):
	"""Service Mode List base class."""
	def __init__(self, game, priority, font):
		super(ServiceModeList, self).__init__(game, priority, font)
		self.items = []
		if self.no_exit_switch:
			self.add_switch_handler(name='down', event_type='closed', delay=None, handler=self.shift_exit)
		else:
			self.add_switch_handler(name='exit', event_type='closed', delay=None, handler=self.exit)

	def mode_started(self):
		super(ServiceModeList, self).mode_started()

		self.iterator = 0
		self.change_item()

	def change_item(self):
		ctr = 0
                for item in self.items:
			if (ctr == self.iterator):
				self.item = item
			ctr += 1
		self.max = ctr - 1
		self.item_layer.set_text(self.item.name)

	def sw_up_closed(self,sw):
		if self.game.machineType != 'sternWhitestar' or self.game.switches.enter.is_open():
			self.item.disable()
			if (self.iterator < self.max):
				self.iterator += 1
			self.game.sound.play('service_next')
			self.change_item()
		return True

	def sw_down_closed(self,sw):
		if self.game.machineType != 'sternWhitestar' or self.game.switches.enter.is_open():
			self.item.disable()
			if (self.iterator > 0):
				self.iterator -= 1
			self.game.sound.play('service_previous')
			self.change_item()
		return True

	def sw_enter_closed(self,sw):
		return True

	def shift_exit(self, sw):
		if self.game.switches.enter.is_closed():
			self.item.disable()
			self.game.modes.remove(self)
			return True

	def exit(self, sw):
		self.item.disable()
		self.game.modes.remove(self)
		return True

class ServiceMode(ServiceModeList):
	"""Service Mode."""
	def __init__(self, game, priority, font):
		super(ServiceMode, self).__init__(game, priority,font)
		self.title_layer.set_text('Service Mode')
		self.lamp_test = LampTest(self.game, self.priority+1, font)
		self.coil_test = CoilTest(self.game, self.priority+1, font)
		self.switch_test = SwitchTest(self.game, self.priority+1, font)
		self.items = [self.switch_test, self.lamp_test, self.coil_test]
		if self.no_exit_switch:
			self.add_switch_handler(name='up', event_type='closed', delay=None, handler=self.shift_enter)
		else:
			self.add_switch_handler(name='enter', event_type='closed', delay=None, handler=self.enter)

	def shift_enter(self, sw):
		if self.game.switches.enter.is_closed():
			self.game.modes.add(self.item)
			return True

	def enter(self,sw):
		self.game.modes.add(self.item)
		return True

class LampTest(ServiceModeList):
	"""Lamp Test"""
	def __init__(self, game, priority, font):
		super(LampTest, self).__init__(game, priority,font)
		self.name = "Lamp Test"
		self.items = self.game.lamps

	def change_item(self):
		super(LampTest, self).change_item()
		self.item.schedule(schedule=0x00ff00ff, cycle_seconds=0, now=True)

class CoilTest(ServiceModeList):
	"""Coil Test"""
	def __init__(self, game, priority, font):
		super(CoilTest, self).__init__(game, priority, font)
		self.name = "Coil Test"
		self.title_layer.set_text('Coil Test - Enter btn: mode')
		self.instruction_layer.set_text('Pulse with start button')
		self.items = self.game.coils

	def mode_started(self):
		super(CoilTest, self).mode_started()
		self.action = 'manual'
		self.game.lamps.startButton.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)
		self.delay(name='auto', event_type=None, delay=2.0, handler=self.process_auto)

	def process_auto(self):
		if (self.action == 'auto'):
			self.item.pulse(20)
		self.delay(name='auto', event_type=None, delay=2.0, handler=self.process_auto)


	def sw_enter_closed(self,sw):
		if (self.action == 'manual'):
			self.action = 'auto'
			self.game.lamps.startButton.disable()
			self.instruction_layer.set_text('Auto pulse')
		elif (self.action == 'auto'):
			self.action = 'manual'
			self.game.lamps.startButton.schedule(schedule=0xff00ff00, cycle_seconds=0, now=False)
			self.instruction_layer.set_text('Pulse with start button')
		return True

	def sw_startButton_closed(self,sw):
		if (self.action == 'manual'):
			self.item.pulse(20)
		return True

class SwitchTest(ServiceModeSkeleton):
	"""Switch Test"""
	def __init__(self, game, priority, font):
		super(SwitchTest, self).__init__(game, priority,font)
		self.name = "Switch Test"
		for switch in self.game.switches:
			if self.game.machineType == 'sternWhitestar':
				add_handler = 1
			elif switch != self.game.switches.exit:
				add_handler = 1
			else:
				add_handler = 0
			if add_handler:
				self.add_switch_handler(name=switch.name, event_type='open', delay=None, handler=self.switch_handler)
				self.add_switch_handler(name=switch.name, event_type='closed', delay=None, handler=self.switch_handler)

	def switch_handler(self, sw):
		if (sw.state):
			self.game.sound.play('service_switch_edge')
		self.item_layer.set_text(sw.name + ' - ' + str(sw.state))
		return True
			

