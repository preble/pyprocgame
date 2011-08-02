import httplib
import urllib
import sys
from clientutil import encode_multipart_formdata
import json # note: requires Python 2.6
#from django.utils import simplejson as json

class MailboxClient:
	def __init__(self, host, port, api_key):
		self.host = host
		self.port = port
		self.api_key = api_key
	
	def connection(self):
		return httplib.HTTPConnection(self.host, self.port)

	def submit_job(self, dmd_data, fpga_base):
		"""docstring for submit_job"""
	
		fields = [('api_key', self.api_key), ('base', fpga_base)]
		files = [('data', 'data.dmd', dmd_data)]
		content_type, body = encode_multipart_formdata(fields, files)
		headers = {"Content-type": content_type, "Accept": "text/plain"}
	
		# print "\n", body, "\n"
	
		conn = self.connection()
		conn.request('POST', '/jobs/new', body, headers)
		resp = conn.getresponse()
		resp_data = resp.read()
		conn.close()
		if resp.status == 200:
			return resp_data
		else:
			print resp.status, resp.reason
			print resp_data
			return None

	def poll_for_result(self, job_key):
		
		params = {'api_key':self.api_key}
	
		conn = self.connection()
		conn.request('GET', '/jobs/%s/result?%s'%(job_key, urllib.urlencode(params)))
		resp = conn.getresponse()
		resp_data = resp.read()
		conn.close()
		return resp_data, resp.status
	
	# Worker Requests
	
	def list_jobs(self, timestamp):
		
		params = {'api_key':self.api_key, 'timestamp':timestamp}
		
		conn = self.connection()
		conn.request('GET', '/jobs/list?'+urllib.urlencode(params))
		resp = conn.getresponse()
		resp_data = resp.read()
		conn.close()
		if resp.status == 200:
			jobs_arr = json.loads(resp_data)
			return jobs_arr
		else:
			print resp.status, resp.reason
			print resp_data
			return None
	
	def get_job_input(self, job_key):
		params = {'api_key': self.api_key}
		conn = self.connection()
		conn.request('GET', '/jobs/%s/request?%s'%(job_key, urllib.urlencode(params)))
		resp = conn.getresponse()
		resp_data = resp.read()
		conn.close()
		if resp.status == 200:
			return resp_data
		else:
			print resp.status, resp.reason
			print resp_data
			return None

	def submit_result(self, job_key, status_code, result_content_type, result_data):

		fields = [('api_key', self.api_key), ('status_code', str(status_code)), ('content_type', result_content_type)]
		files = [('data', 'filename', result_data)]
		content_type, body = encode_multipart_formdata(fields, files)
		headers = {"Content-type": content_type, "Accept": "text/plain"}

		# print "\n", body, "\n"

		conn = self.connection()
		conn.request('POST', '/jobs/%s/result'%(job_key), body, headers)
		resp = conn.getresponse()
		resp_data = resp.read()
		conn.close()
		if resp.status == 200:
			return resp_data
		else:
			print resp.status, resp.reason
			print resp_data
			return None


def main():
	command = sys.argv[1]
	api_key = sys.argv[2]
	client = MailboxClient(host='127.0.0.1', port=8084, api_key=api_key)
	
	if command == 'submit':
		dmd_path = sys.argv[3]
		fpga_base = sys.argv[4]
		#wm_x = sys.argv[5]
		#wm_y = sys.argv[6]

		with open(dmd_path, 'rb') as f:
			dmd_data = f.read()

		print 'length:', len(dmd_data)

		#job_key = client.submit_job(dmd_data, fpga_base, wm_x, wm_y)
		job_key = client.submit_job(dmd_data, fpga_base)
		print 'Got job key:', job_key

	elif command == 'list':
		timestamp = sys.argv[3]
		jobs = client.list_jobs(timestamp)
		for job in jobs:
			print job['timestamp'], job['job_key']
	
	elif command == 'get_result':
		job_key = sys.argv[3]
		data = client.poll_for_result(job_key)
		if data:
			print 'get_result got %d bytes'%(len(data))
		else:
			print 'no result'
	
	elif command == 'put_result':
		job_key = sys.argv[3]
		status_code = sys.argv[4]
		content_type = sys.argv[5]
		filename = sys.argv[6]
		with open(filename, 'rb') as f:
			client.submit_result(job_key, status_code, content_type, f.read())
	
	else:
		print 'Unrecognized command.'


if __name__ == "__main__":
	main()
