#!/usr/bin/python
import argparse
from cStringIO import StringIO
import os
import pycurl
import re
import sys
from urlparse import urlparse

BAD_URL=0
CODE_200=1
CODE_404=2
CODE_500=3

class Url:
    def __init__(self,url,response_code = -1):
        self.url = url
        self.response_code = response_code
	url = None
	response_code = -1

def isDomainNameValid ( name ):
  # TODO: Works but accepts hostnames with a name of at least 3 characters with no domain. ie. www instead of www.test.com
  #regex = re.compile(r'(?=^.{1,254}$)(^(?:(?!\d+\.|-)[a-zA-Z0-9_\-]{1,63}(?<!-)\.)+(?:[a-zA-Z]{2,})$)', re.IGNORECASE)
  regex = re.compile(r'[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,4}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?', re.IGNORECASE)

  if regex.match(name):
    return True
  else:
    return False

def isURLValid(url) :
  regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
  if regex.match(url):
    return True
  else:
    return False
 
def isPathValid(strg, search=re.compile(r'^\/[/.a-zA-Z0-9-~]*$').search):
  return bool(search(strg))    

def isIPAddressValid(strg):
  regex = re.compile(r'(([2]([0-4][0-9]|[5][0-5])|[0-1]?[0-9]?[0-9])[.]){3}(([2]([0-4][0-9]|[5][0-5])|[0-1]?[0-9]?[0-9]))')
  #Allow the special "all networks" network format 0/0
  if regex.match(strg) or strg == "0/0" or strg == "!0/0":
    return True
  else:
    return False

def isPortValid(port):
  if port.isdigit() and int(port) <= 65536:
    return True
  else:
    return False
   
def parseURL(url):
  if url:
    return urlparse(url)
  else:
    return None


def openFile(filename, mode = 'r'):
#	if not mode:
#		mode = 'r'	
	if os.path.exists(filename):
		with open(filename) as urls:
		#urls = open(filename, mode)			
			lineas = urls.readlines()
		#urls.close()
	else:
		print "ERROR: File not found."
		sys.exit(1)
	return lineas


def saveFile(filename,content):
        arch = open(filename, 'w')
        try:
            arch.write(content)
        finally:	
            arch.close()

def testUrls(validUrls, invalidUrls):
	urls = validUrls # list of urls
	reqs: List of individual requests.
	Each list element will be a 3-tuple of url (string), response string buffer
	(cStringIO.StringIO), and request handle (pycurl.Curl object).
	reqs = [] 

	Build multi-request object.
	m = pycurl.CurlMulti()
	for url in urls: 
		response = StringIO()
		header = StringIO()
		handle = pycurl.Curl()
		handle.setopt(pycurl.URL, url.url)
		handle.setopt(pycurl.WRITEFUNCTION, response.write)
		handle.setopt(pycurl.HEADERFUNCTION, header.write)
		req = (url, response, handle)
		Note that the handle must be added to the multi object
		by reference to the req tuple (threading?).
		m.add_handle(req[2])
		reqs.append(req)

	Perform multi-request.
	This code copied from pycurl docs, modified to explicitly
	set num_handles before the outer while loop.
	SELECT_TIMEOUT = 5.0
	num_handles = len(reqs)
	while num_handles:
		ret = m.select(SELECT_TIMEOUT)
		if ret == -1:
			continue
		while 1:
			ret, num_handles = m.perform()
			if ret != pycurl.E_CALL_MULTI_PERFORM: 
				break
	
	def __get_url(url,url2):
		if url != url2 :
			return True
		else:
			return False
	
	i = 0
	for req in reqs:
		print req[1].getvalue()
		print req[0] + "->" + `req[2].getinfo(pycurl.HTTP_CODE)`
		if req[2].getinfo(pycurl.HTTP_CODE) != CODE_200 :
			validUrls = filter(__get_url,req[0], validUrls[i])
			new_invalid_url = Url(req[0].url,req[2].getinfo(pycurl.HTTP_CODE))
			reqs.remove(req[0])
			invalidUrls.append(new_invalid_url)
		i +=1	
	return reqs[0]
    
def writeInvalidFile(filename,invalidLines):
	content=""
	
	for i in invalidLines:
		content += i.url + "," + `i.response_code` + "\r\n"
	saveFile(filename, content)

def writeValidFile(filename,validLines):
	content=""
	
	for i in validLines:
		content += i.url + "\r\n"
	saveFile(filename, content)
	
	
def parseFile(filename, validLines, invalidLines):
	lines = openFile(filename)
	
	for i in lines:
		i = i.strip()
		url = Url(i)
		
		if not isURLValid(i):
			if not isDomainNameValid(i):
				#print "INVALID URL: " + i
				url.response_code = -1
				invalidLines.append(url)
			else:
				parsed_url = urlparse(i)
				if not parsed_url.scheme == "http" and not parsed_url.scheme == "https":
					url.url = "http://" + i					
#				if not url.scheme == "https" :
#					i = "https://" + i
				validLines.append(url)
		else:
			#print "VALID URL=" + i
			validLines.append(url)

def search(args):
	validLines = []
	invalidLines = []
	print "Input file: " + args.source_file[0]
	print "Output file: " + args.dest_file[0]
	print "Invalid URL's file: " + args.invalid_file[0] + "\n"
	print "Starting URL validation...\n"
	
	#Step 1: Load the file and split valid lines from malformed ones
	parseFile(args.source_file[0], validLines, invalidLines)
	print "Number of valid URL's: " + `len(validLines)`
	print "Number of invalid URL's: " + `len(invalidLines)`

	#Step 2: Test valid URL's and split the invalid ones (anything that)
	#doesn't returns a HTTP 200 ok code.
	testUrls(validLines, invalidLines)
	
	#Step 3: Save new lists to their respective files
	writeInvalidFile(args.invalid_file[0], invalidLines)
	writeValidFile(args.dest_file[0], validLines)


def run():
  # create the top-level parser
  parser = argparse.ArgumentParser(description='Apukay Security URL Validator Tool.', 
				  epilog='Apukay Security. - All rights reserved 2014')
  parser.add_argument('-s', '--source', 
		      dest='source_file', 
		      nargs=1, 
		      help='Path to file containing URL\'s to validate.', 
		      required=True)
  parser.add_argument('-d', '--dest', 
		      dest='dest_file', 
		      nargs=1, 
		      help='Name of file containing the list of valid URL\'s.', 
		      required=True)
  parser.add_argument('-i', '--invalid', 
		      dest='invalid_file', 
		      nargs=1, 
		      help='Name of file containing the list of invalid URL\'s.', 
		      required=True)  
  parser.add_argument('--verbose', '-v', 
		      action='count', 
		      help='Verbose output. -vv debug output')
  parser.add_argument('--version', action='version', version='urlvalidator 0.1 \n')		    

  parser.set_defaults(func=search)
  args = parser.parse_args()
  args.func(args)

if __name__ == "__main__":
  run()