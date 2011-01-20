import os
import sys
import logging
import yaml
import pinproc
import procgame.game
import procgame.lamps
import procgame.tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class LampGame(procgame.game.GameController):
	
	show_filename = None
	show_mtime = None
	
	def __init__(self, machine_type):
		super(LampGame, self).__init__(machine_type)
		self.lampctrl = procgame.lamps.LampController(game=self)
	
	def play(self, filename):
		self.show_filename = filename
		self.show_mtime = None
	
	def tick(self):
		super(LampGame, self).tick()
		mtime = os.path.getmtime(self.show_filename)
		if self.show_mtime != mtime:
			logging.getLogger('').info('Loading lamp show at %s.', self.show_filename)
			self.lampctrl.register_show('show', self.show_filename)
			self.lampctrl.play_show('show', repeat=True)
			self.show_mtime = mtime

def play(config_path, show_path):
	game = LampGame(machine_type=procgame.tools.machine_type_from_yaml(config_path))
	game.load_config(config_path)
	game.play(show_path)
	game.run_loop()
	del game


def tool_populate_options(parser):
	parser.add_option('-c', '--config', action='store', help='Path to the YAML machine configuration file.')

def tool_get_usage():
	return """<file.lampshow>"""

def tool_run(options, args):
	if len(args) != 1:
		return False
	
	if not options.config:
		sys.stderr.write('No configuration file specified.\n')
		return False
	
	return play(config_path=options.config, show_path=args[0])
