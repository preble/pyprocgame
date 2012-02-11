import logging
import pinproc
import re

class Switch(object):
	def __init__(self, pdb, number_str):
		upper_str = number_str.upper()
		if upper_str.startswith('SD'):
			self.sw_type = 'dedicated'
			self.sw_number = int(upper_str[2:])
		elif '/' in upper_str:
			self.sw_type = 'matrix'
			self.sw_number = self.parse_matrix_num(upper_str)
		else:
			self.sw_type = 'proc'
			self.sw_number = int(number_str)
	
	def proc_num(self):
		return self.sw_number

	def parse_matrix_num(self, num_str):
		cr_list = num_str.split('/')
		return (32 + int(cr_list[0])*16 + int(cr_list[1]))

class Coil(object):
	def __init__(self, pdb, number_str):
		self.pdb = pdb
		upper_str = number_str.upper()
		if self.is_direct_coil(upper_str):
			self.coil_type = 'dedicated'
			self.banknum = (int(number_str[1:]) - 1)/8
			self.outputnum = int(number_str[1:])
		elif self.is_pdb_coil(number_str):
			self.coil_type = 'pdb'
			(self.boardnum, self.banknum, self.outputnum) = decode_pdb_address(number_str, self.pdb.aliases)
		else: 
			coil_type = 'unknown'

	
	def bank(self):
		if self.coil_type == 'dedicated': 
			return self.banknum
		elif self.coil_type == 'pdb': 
			return self.boardnum*2 + self.banknum
		else:
			return -1
	def output(self):
		return self.outputnum

	def is_direct_coil(self, string):
		if len(string) < 2 or len(string) > 3: return False
		if not string[0] == 'C': return False 
		if not string[1:].isdigit(): return False
		return True

	def is_pdb_coil(self, string):
		return is_pdb_address(string, self.pdb.aliases)

class Lamp(object):
	def __init__(self, pdb, number_str):
		self.pdb = pdb
		upper_str = number_str.upper()
		if self.is_direct_lamp(upper_str):
			self.lamp_type = 'dedicated'
			self.output = int(number_str[1:])
		elif self.is_pdb_lamp(number_str): # C-Ax-By-z:R-Ax-By-z  or  C-x/y/z:R-x/y/z
			self.lamp_type = 'pdb'
			source_addr, sink_addr = self.split_matrix_addr_parts(number_str)
			(self.source_boardnum, self.source_banknum, self.source_outputnum) = decode_pdb_address(source_addr, self.pdb.aliases)
			(self.sink_boardnum, self.sink_banknum, self.sink_outputnum) = decode_pdb_address(sink_addr, self.pdb.aliases)
		else:
			self.lamp_type = 'unknown'

	def source_board(self):
		return self.source_boardnum
	def sink_board(self):
		return self.sink_boardnum
	def source_bank(self):
		return self.source_boardnum*2 + self.source_banknum
	def sink_bank(self):
		return self.sink_boardnum*2 + self.sink_banknum
	def source_output(self):
		return self.source_outputnum
	def sink_output(self):
		return self.sink_outputnum
	def dedicated_bank(self):
		return self.banknum
	def dedicated_output(self):
		return self.output

	def is_direct_lamp(self, string):
		if len(string) < 2 or len(string) > 3: return False
		if not string[0] == 'L': return False 
		if not string[1:].isdigit(): return False
		return True

	def split_matrix_addr_parts(self, string):
		# Input is of form C-Ax-By-z:R-Ax-By-z  or  C-x/y/z:R-x/y/z  or  aliasX:aliasY
		# We want to return only the address part: Ax-By-z, x/y/z, or aliasX.  That is, remove the two character prefix if present.
		addrs = string.rsplit(':')
		if len(addrs) is not 2:
			return []
		addrs_out = []
		for addr in addrs:
			bits = addr.split('-')
			if len(bits) is 1:
				addrs_out.append(addr) # Append unchanged.
			else:                                    # Generally this will be len(bits) 2 or 4.
				addrs_out.append('-'.join(bits[1:])) # Remove the first bit and rejoin.
		return addrs_out

	def is_pdb_lamp(self, string):
		params = self.split_matrix_addr_parts(string)
		if len(params) != 2: return False
		for addr in params:
			if not is_pdb_address(addr, self.pdb.aliases):
				print "not pdb address!", addr
				return False
		return True

class PDBConfig(object):
	indexes = []
	proc = None
	aliases = None # set in __init__
	"""Loaded from ``PRDriverAliases`` section of config in :meth:`__init__`."""
	
	def __init__(self, proc, config):

		self.logger = logging.getLogger('game.pdb')
		self.logger.info("Configuring P-ROC to work with PDBs")

		self.proc = proc

		# Grab globals from the config data
		self.get_globals(config)

		# Initialize some lists for data collecting
		coil_bank_list = []
		lamp_source_bank_list = []
		lamp_list = []
		lamp_list_for_index = []
		
		self.aliases = []
		if 'PRDriverAliases' in config:
			for alias_dict in config['PRDriverAliases']:
				alias = DriverAlias(alias_dict['expr'], alias_dict['repl'])
				self.aliases.append(alias)

		# Make a list of unique coil banks
		for name in config['PRCoils']:
			item_dict = config['PRCoils'][name]
			coil = Coil(self, str(item_dict['number']))
			if coil.bank() not in coil_bank_list:
				coil_bank_list.append(coil.bank())

		# Make a list of unique lamp source banks.  The P-ROC only supports 2.
		# TODO: What should be done if 2 is exceeded?
		for name in config['PRLamps']:
			item_dict = config['PRLamps'][name]
			lamp = Lamp(self, str(item_dict['number']))

			# Catalog PDB banks
			# Dedicated lamps don't use PDB banks.  They use P-ROC direct
			# driver pins.  
			if lamp.lamp_type == 'dedicated':
				pass

			elif lamp.lamp_type == 'pdb':
				if lamp.source_bank() not in lamp_source_bank_list:
					lamp_source_bank_list.append(lamp.source_bank())
	
	
				# Create dicts of unique sink banks.  The source index is needed when
				# setting up the driver groups.
				lamp_dict = {'source_index': lamp_source_bank_list.index(lamp.source_bank()), 'sink_bank': lamp.sink_bank(), 'source_output': lamp.source_output()}
	
				# lamp_dict_for_index.  This will be used later when the p-roc numbers
				# are requested.  The requestor won't know the source_index, but it will
				# know the source board.  This is why two separate lists are needed.
				lamp_dict_for_index = {'source_board': lamp.source_board(), 'sink_bank': lamp.sink_bank(), 'source_output': lamp.source_output()}
	
				if lamp_dict not in lamp_list:
					lamp_list.append(lamp_dict)
					lamp_list_for_index.append(lamp_dict_for_index)

		# Create a list of indexes.  The PDB banks will be mapped into this list.
		# The index of the bank is used to calculate the P-ROC driver number for
		# each driver.
		num_proc_banks = pinproc.DriverCount/8
		self.indexes = [99] * num_proc_banks

		self.initialize_drivers(proc)

		# Set up dedicated driver groups (groups 0-3).
		for group_ctr in range(0,4):
			# TODO: Fix this.  PDB Banks 0-3 are also interpreted as dedicated bank here.
			enable =  group_ctr in coil_bank_list
			self.logger.info("Driver group %02d (dedicated): Enable=%s", group_ctr,enable)
			proc.driver_update_group_config(group_ctr,
							0,
							group_ctr,
							0,
							0,
							False,
							True,
							enable,
							True)

		group_ctr += 1

		# Process lamps first.  The P-ROC can only control so many drivers directly.
		# Since software won't have the speed to control lamp matrixes, map the lamps
		# first.  If there aren't enough P-ROC driver groups for coils, the overflow
		# coils can be controlled by software via VirtualDrivers (which should get
		# set up automatically by this code.

		for i,lamp_dict in enumerate(lamp_list):
			# If the bank is 16 or higher, the P-ROC can't control it directly. 
			# SW can't really control lamp matrixes either (need microsecond
			# resolution).  Instead of doing crazy logic here for a case that
			# probably won't happen, just ignore these banks.
			if (group_ctr >= num_proc_banks or lamp_dict['sink_bank'] >= 16):
				self.logger.error("Lamp matrix banks can't be mapped to index %d because that's outside of the banks the P-ROC can control.", lamp_dict['sink_bank'])
			else:
				self.logger.info("Driver group %02d (lamp sink): slow_time=%d enable_index=%d row_activate_index=%d row_enable_index=%d matrix=%s", group_ctr, self.lamp_matrix_strobe_time, lamp_dict['sink_bank'], lamp_dict['source_output'], lamp_dict['source_index'], True )
				self.indexes[group_ctr] = lamp_list_for_index[i]
				proc.driver_update_group_config(group_ctr,
								self.lamp_matrix_strobe_time,
								lamp_dict['sink_bank'],
								lamp_dict['source_output'],
								lamp_dict['source_index'],
								True,
								True,
								True,
								True)
				group_ctr += 1
	

		for coil_bank in coil_bank_list:
			# If the bank is 16 or higher, the P-ROC can't control it directly. SW
			# will have do the driver logic and write any changes to the PDB bus.
			# Therefore, map these banks to indexes above the P-ROC's driver count,
			# which will force the drivers to be created as VirtualDrivers.
			# Appending the bank avoids conflicts when group_ctr gets too high.
			if (group_ctr >= num_proc_banks or coil_bank >= 16):
				self.logger.warning("Driver group %d mapped to driver index outside of P-ROC control.  These Drivers will become VirtualDrivers.  Note, the index will not match the board/bank number; so software will need to request those values before updating the drivers.", coil_bank)
				self.indexes.append(coil_bank)
			else:
				self.logger.info("Driver group %02d: slow_time=%d Enable Index=%d", group_ctr, 0, coil_bank)
				self.indexes[group_ctr] = coil_bank
				proc.driver_update_group_config(group_ctr,
								0,
								coil_bank,
								0,
								0,
								False,
								True,
								True,
								True)
				group_ctr += 1
		
		for i in range(group_ctr, 26):
			self.logger.info("Driver group %02d: disabled", i)
			proc.driver_update_group_config(i,
							self.lamp_matrix_strobe_time,
							0,
							0,
							0,
							False,
							True,
							False,
							True)
		
		# Make sure there are two indexes.  If not, fill them in.
		while len(lamp_source_bank_list) < 2: lamp_source_bank_list.append(0)

		# Now set up globals.  First disable them to allow the P-ROC to set up
		# the polarities on the Drivers.  Then enable them.
		self.configure_globals(proc, lamp_source_bank_list, False)
		self.configure_globals(proc, lamp_source_bank_list, True)

	def initialize_drivers(self, proc):
		# Loop through all of the drivers, initializing them with the polarity.
		for i in range(0, 208):
			state = {'driverNum': i,
       	                'outputDriveTime': 0,
       	                'polarity': True,
       	                'state': False,
       	                'waitForFirstTimeSlot': False,
       	                'timeslots': 0,
       	                'patterOnTime': 0,
       	                'patterOffTime': 0,
       	                'patterEnable': False,
       	                'futureEnable': False}
	
			proc.driver_update_state(state)


	def get_globals(self, config):
		if 'lamp_matrix_strobe_time' in config['PRDriverGlobals']:
			self.lamp_matrix_strobe_time = int(config['PRDriverGlobals']['lamp_matrix_strobe_time'])
		else:
			self.lamp_matrix_strobe_time = 200

		if 'watchdog_time' in config['PRDriverGlobals']:
			self.watchdog_time = int(config['PRDriverGlobals']['watchdog_time'])
		else:
			self.watchdog_time = 1000

		if 'use_watchdog' in config['PRDriverGlobals']:
			self.use_watchdog = bool(config['PRDriverGlobals']['use_watchdog'])
		else:
			self.use_watchdog = True


	def configure_globals(self, proc, lamp_source_bank_list, enable=True):
		
		if enable: self.logger.info("Configuring PDB Driver Globals:  polarity = %s  matrix column index 0 = %d  matrix column index 1 = %d", True, lamp_source_bank_list[0], lamp_source_bank_list[1]);
		proc.driver_update_global_config(enable, # Don't enable outputs yet
						True,  # Polarity
						False, # N/A
						False, # N/A
						1, # N/A
						lamp_source_bank_list[0],
						lamp_source_bank_list[1],
						False, # Active low rows? No
						False, # N/A
						False, # Stern? No
						False, # Reset watchdog trigger
						self.use_watchdog, # Enable watchdog
						self.watchdog_time)

		# Now set up globals
		proc.driver_update_global_config(True, # Don't enable outputs yet
						True,  # Polarity
						False, # N/A
						False, # N/A
						1, # N/A
						lamp_source_bank_list[0],
						lamp_source_bank_list[1],
						False, # Active low rows? No
						False, # N/A
						False, # Stern? No
						False, # Reset watchdog trigger
						self.use_watchdog, # Enable watchdog
						self.watchdog_time)
			
	# Return the P-ROC number for the requested driver string.
	# This method uses the driver string to look in the indexes list that
	# was set up when the PDBs were configured.  The resulting P-ROC index * 3
	# is the first driver number in the group, and the driver offset is added
	# to that.
	def get_proc_number(self, section, number_str):
		if section == 'PRCoils':
			coil = Coil(self, number_str)
			bank = coil.bank()
			if bank == -1: return (-1)
			index = self.indexes.index(coil.bank())
			num = index * 8 + coil.output()
			return num

		if section == 'PRLamps':
			lamp = Lamp(self, number_str)
			if lamp.lamp_type == 'unknown': return (-1)
			elif lamp.lamp_type == 'dedicated': 
				return lamp.dedicated_output()

			lamp_dict_for_index = {'source_board': lamp.source_board(), 'sink_bank': lamp.sink_bank(), 'source_output': lamp.source_output()}
			if lamp_dict_for_index not in self.indexes: return -1
			index = self.indexes.index(lamp_dict_for_index)
			num = index * 8 + lamp.sink_output()
			return num

		if section == 'PRSwitches':
			switch = Switch(self, number_str)
			num = switch.proc_num()
			return num


class DriverAlias(object):
	def __init__(self, key, value):
		self.expr = re.compile(key)
		self.repl = value

	def matches(self, addr):
		return self.expr.match(addr)

	def decode(self, addr):
		return self.expr.sub(repl=self.repl, string=addr)


def is_pdb_address(addr, aliases=[]):
	"""Returne True if the given address is a valid PDB address."""
	try:
		t = decode_pdb_address(addr=addr, aliases=aliases)
		return True
	except:
		return False

def decode_pdb_address(addr, aliases=[]):
	"""Decodes Ax-By-z or x/y/z into PDB address, bank number, and output number.

	Raises a ValueError exception if it is not a PDB address, otherwise returns a tuple of (addr, bank, number).
	"""
	for alias in aliases:
		if alias.matches(addr):
			addr = alias.decode(addr)
			break

	if '-' in addr: # Ax-By-z form
		params = addr.rsplit('-')
		if len(params) != 3:
			raise ValueError, 'pdb address must have 3 components'
		board = int(params[0][1:])
		bank = int(params[1][1:])
		output = int(params[2][0:])
		return (board, bank, output)

	elif '/' in addr: # x/y/z form
		params = addr.rsplit('/')
		if len(params) != 3:
			raise ValueError, 'pdb address must have 3 components'
		board = int(params[0])
		bank = int(params[1])
		output = int(params[2])
		return (board, bank, output)

	else:
		raise ValueError, 'PDB address delimeter (- or /) not found.'
