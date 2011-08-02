import os
import sys
import time
import bz2
import StringIO
from procgame import dmd
from mailbox import *
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

POLL_DELAY = 5
HOST = 'procmailbox000.appspot.com'
PORT = 80
# HOST = '127.0.0.1'
# PORT = 8084

class JobSubmitter(object):
	def __init__(self, host, port, api_key):
		self.logger = logging.getLogger('worker')
		self.client = mailboxclient.MailboxClient(host, port, api_key)
	
	def submit(self, fpga_base, input_path, output_path):
		"""docstring for run_worker"""
		
		with open(input_path, 'rb') as f:
			job_key = self.client.submit_job(f.read(), json.dumps(fpga_base))
		
		if job_key == None:
			self.logger.error('Error submitting request.')
			return
		
		self.logger.info('Request submitted; waiting...')
		
		data = None
		
		while True:
			time.sleep(POLL_DELAY)
			self.logger.info('Checking...')
			data, status = self.client.poll_for_result(job_key)
			if status == 200:
				break
			elif status == 202:
				continue
			else:
				self.logger.error('Request failed with status %d: %s', status, data)
				return
		
		self.logger.info('Image received!')
		
		with open(output_path, 'wb') as f:
			f.write(bz2.decompress(data))

def tool_get_usage():
	return """[options] <key> <base_fpga_version> <file.dmd> <watermark_x> <watermark_y> <output.p-roc>


Parameters:
  key: A transaction key obtained from support@pinballcontrollers.com.
  base_fpga_version: Version number of the desired base P-ROC FPGA image.  Format is x.yy (ie: 1.18).
  file.dmd: Splash screen image in the .dmd format - must be 128x32.
  [optional: watermark_x]: Leftmost X coordinate of the P-ROC version watermark.  0 <= x <= 91.
  [optional: watermark_y]: Uppermost Y coordinate of the P-ROC version watermark.  0 <= y <= 26.
  output.p-roc: Filename for the new FPGA image.  Must end in \".p-roc\".
"""

def tool_populate_options(parser):
	pass

def check_params(fpga_base, input_path, output_path):

        # Make sure fpga_base is x.yy with digits only
	fpga_base_list = str.split(fpga_base['fpga_base'], '.')
	if len(fpga_base_list) != 2: return 0
	if not fpga_base_list[0].isdigit() or not fpga_base_list[1].isdigit(): return 0

	# Make sure input path is a .dmd filename
	if not input_path.endswith(".dmd"): return 0
	if not os.path.isfile(input_path):
		print("\n\nERROR: Invalid filename: %s"%(input_path))
		return 0
	else:
		# Check .dmd file dimensions
		f = open(input_path, 'rb')
		anim = dmd.Animation()
		anim.populate_from_dmd_file(StringIO.StringIO(f.read()))
		frame = anim.frames[0]
		if frame.width != 128 or frame.height != 32:
			print("\n\nERROR: .dmd file must be 128x32")
			return 0

	# Make sure requested watermark position is valid
	wm_x = fpga_base['wm_x']
	wm_y = fpga_base['wm_y']
	if wm_x < 0 or wm_x > 91 or wm_y < 0 or wm_y > 26:
		print("\n\nERROR: Invalid Watermark coordinates.")
		print wm_x
		print wm_y
		return 0

	# Make sure output path is a .p-roc filename
	if not output_path.endswith(".p-roc"): return 0


def tool_run(options, args):
	if len(args) != 4 and len(args) != 6:
		print("\nERROR: Invalid parameters")
		tool_get_usage()
	else:
		api_key = args[0]
		input_path = args[2]
		fpga_base_dict = {}
		if len(args) == 4:
			fpga_base_dict['fpga_base'] = args[1]
			fpga_base_dict['wm_x'] = 46
			fpga_base_dict['wm_y'] = 26
			output_path = args[3]
		else:
			fpga_base_dict['fpga_base'] = args[1]
			fpga_base_dict['wm_x'] = int(args[3])
			fpga_base_dict['wm_y'] = int(args[4])
			output_path = args[5]


		if (check_params(fpga_base_dict, input_path, output_path)==0):
			print("\nERROR: Invalid parameters")
			tool_get_usage()
		else:
			jobber = JobSubmitter(HOST, PORT, api_key)
			jobber.submit(fpga_base_dict, input_path, output_path)
			return True
