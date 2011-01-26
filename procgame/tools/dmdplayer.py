import sys
import os
import pinproc
import procgame.game
import procgame.dmd
import time
import logging

logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class PlayerGame(procgame.game.BasicGame):
	
	anim_layer = None
	
	def __init__(self, machine_type):
		super(PlayerGame, self).__init__(machine_type)
		self.anim_layer = procgame.dmd.AnimatedLayer()
		mode = procgame.game.Mode(game=self, priority=1)
		mode.layer = self.anim_layer
		self.modes.add(mode)
	
	def play(self, filename, repeat):
		anim = procgame.dmd.Animation().load(filename)
		self.anim_layer.frames = anim.frames
		self.anim_layer.repeat = repeat
		if not repeat:
			self.anim_layer.add_frame_listener(-1, self.end_of_animation)
	
	def end_of_animation(self):
		self.end_run_loop()


def tool_populate_options(parser):
	parser.add_option('-m', '--machine-type', action='store', help='wpc, wpc95, stermSAM, sternWhitestar or custom (default)')
	parser.add_option('-r', '--repeat', action='store_true', help='Repeat the animation indefinitely')

def tool_get_usage():
    return """<file.dmd>"""

def tool_run(options, args):
	if len(args) != 1:
		return False
	
	if options.machine_type:
		machine_type = pinproc.normalize_machine_type(options.machine_type)
	else:
		machine_type = pinproc.MachineTypeCustom
	
	game = PlayerGame(machine_type=machine_type)
	
	game.play(filename=args[0], repeat=options.repeat)
	
	game.run_loop()
	del game
	return True
