#!/usr/bin/python
import argparse
from cStringIO import StringIO
import os
import re
import sys
from urlparse import urlparse
from twisted.internet import reactor, threads
import httplib
import itertools

concurrent = 400
finished=itertools.count(1)
reactor.suggestThreadPoolSize(concurrent)
added=0
valid_urls = {}
invalid_urls = {}

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

def testUrls():
	global added
	for url in valid_urls:
		added+=1
		addTask(url)

	try:
		reactor.run()
	except KeyboardInterrupt:
		reactor.stop()


def getStatus(ourl):
    url = urlparse(ourl)
    conn = httplib.HTTPConnection(url.netloc)   
    conn.request("HEAD", url.path)
    res = conn.getresponse()
    return res.status

def processResponse(response,url):
	global invalid_urls
	if response == 200 or response == 301 or response == 302 :
		valid_urls[url] = response
	else :
		invalid_urls[url] = response
		del valid_urls[url]
	processedOne()

def processError(error,url):
    invalid_urls[url] = error.getErrorMessage()
    processedOne()

def processedOne():
	global added
	if finished.next()==added:
		reactor.stop()

def addTask(url):
    req = threads.deferToThread(getStatus, url)
    req.addCallback(processResponse, url)
    req.addErrback(processError, url)   
    
def writeInvalidFile(filename):
	global invalid_urls
	content=""
	
	for url in invalid_urls:
		content += url + "," + `invalid_urls[url]` + "\r\n"
	saveFile(filename, content)

def writeValidFile(filename):
	global valid_urls
	content=""
	
	for url in valid_urls:
		content += url + "," + `valid_urls[url]` + "\r\n"
	saveFile(filename, content)
	
	
def parseFile(filename):
	lines = openFile(filename)
	global valid_urls,invalid_urls
	
	for url in lines:
		url = url.strip()
		
		if not isURLValid(url):
			if not isDomainNameValid(url):
				invalid_urls[url] = 'MALFORMED'
				
			else:
				parsed_url = urlparse(url)
				if not parsed_url.scheme == "http" and not parsed_url.scheme == "https":
					url = "http://" + url
				valid_urls[url] = ''
		else:
			valid_urls[url] = ''

def search(args):
	validLines = []
	invalidLines = []
	print "Input file: " + args.source_file[0]
	print "Output file: " + args.dest_file[0]
	print "Invalid url's file: " + args.invalid_file[0] + "\n"
	print "Starting url validation...\n"
	
	#Step 1: Load the file and split valid lines from malformed ones
	parseFile(args.source_file[0])
	print "Number of valid url's: " + `len(valid_urls)`
	#TODO # of fixed urls
	print "Number of malformed url's: " + `len(invalid_urls)`

	#Step 2: Test valid URL's and split the invalid ones (anything that)
	#doesn't returns a HTTP 200 ok code.
	print "\nStarting to test valid url's..."
	testUrls()
	print "\nDone"
	
	print "\nWriting results to output files..."
	#Step 3: Save new lists to their respective files
	writeInvalidFile(args.invalid_file[0])
	writeValidFile(args.dest_file[0])


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