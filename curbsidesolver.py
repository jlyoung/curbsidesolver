import logging
import requests
import types
from optparse import OptionParser
from retrying import retry
from urlparse import urljoin

headers = {'session': None}
secret_message = []

def main():
	"""Solve the shopcurbside.com challenge."""
	global headers, secret_message
	usage = 'usage: %prog [options]'
	parser = OptionParser(usage=usage)
	parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
						help='Enable verbose logging.')
	(options, args) = parser.parse_args()
	FORMAT = "%(message)s"
	if options.verbose is None:
		logging.disable(logging.DEBUG)
	else:
		logging.disable(logging.NOTSET)
		logging.basicConfig(level=logging.DEBUG, format=FORMAT)
	print "Running..."
	session = get_session()
	headers['session'] = session
	start_url = 'http://challenge.shopcurbside.com/start'
	request_get_start = requests.get(start_url, headers=headers)
	logging.debug(request_get_start.text)
	response = request_get_start.json()
	next_key = 'next'
	# Handle the case where 'next' key has weird capitalization, i.e. 'nExt'
	for resp_key in response.keys():
		if resp_key.lower() == 'next':
			next_key = resp_key
	if isinstance(response[next_key], types.StringTypes):
		visit_id(response[next_key])
	else:
		for id in response[next_key]:
			visit_id(id)
	print 'SECRET MESSAGE: {secret_message}'.format(secret_message=''.join(secret_message))
		

def retry_on_httperror(exc):
	"""Re-populate the session ID in the headers dict with a new session and retry visit_id()."""
	global headers
	session = get_session()
	headers['session'] = session
	return isinstance(exc, requests.HTTPError)
		
@retry(retry_on_exception=retry_on_httperror, wait_exponential_multiplier=1000, wait_exponential_max=10000)
def visit_id(id_to_visit):
	"""Issue and HTTTP GET request to the supplied id. Append the secret message if it exists. Visit other ids found in the results."""
	global headers, secret_message
	url = urljoin('http://challenge.shopcurbside.com/', id_to_visit)
	request_get_id = requests.get(url, headers=headers)
	logging.debug(request_get_id.text)
	request_get_id.raise_for_status()
	response = request_get_id.json()
	if 'secret' in response:
		secret_message.append(response['secret'])
		logging.debug('SECRET: {secret_char}'.format(secret_char=response['secret']))
	else:
		next_key = 'next'
		for resp_key in response.keys():
			if resp_key.lower() == 'next':
				next_key = resp_key
		if next_key in response:
			if isinstance(response[next_key], types.StringTypes):
				visit_id(response[next_key])
			else:
				for id in response[next_key]:
					visit_id(id)

	
def get_session():
	"""Get and return a new session id."""
	get_session_url = 'http://challenge.shopcurbside.com/get-session'
	request_session = requests.get(get_session_url)
	logging.debug(request_session.text)
	return request_session.text
	
if __name__ == '__main__':
	main()