import pinproc

class AuxPort(object):

	def __init__(self,game):
		super(AuxPort, self).__init__()

		self.game = game
		self.commands = []

		self.init_aux_mem()

	def init_aux_mem(self):
		commands = []
		commands += [pinproc.aux_command_disable()]

		for j in range(1,255):
			commands += [pinproc.aux_command_jump(0)]

		self.game.proc.aux_send_commands(0,commands)

	def get_index(self):
		new_list = []
		self.commands += [None]
		return len(self.commands) - 1

	def update(self, index, commands):
		self.commands[index] = commands
		self.write_commands()

	def write_commands(self):

		# Initialize command list and disable the first end so program
		# doesn't start 'running' until fully written.
		commands = []
		commands += [pinproc.aux_command_disable()]

		for command_set in self.commands:
			if command_set: commands += command_set

		commands += [pinproc.aux_command_jump(0)]
		self.game.proc.aux_send_commands(0,commands)

		commands = []
		commands += [pinproc.aux_command_jump(1)]
		self.game.proc.aux_send_commands(0,commands)

		if True: self.print_commands(commands)

	def print_commands(self, commands):
		ctr = 0
		print "AuxPort commands being written:"
		for command in commands:
			print "Command %d: %s" % (ctr, command)
			ctr += 1

