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
original_urls = None
valid_urls = {}
invalid_urls = {}
fixed_url_counter = 0

def isDomainNameValid ( name ):
  # TODO: Works but accepts hostnames with a name of at least 3 characters with no domain. ie. www instead of www.test.com
	#regex = re.compile(r'(?=^.{1,254}$)(^(?:(?!\d+\.|-)[a-zA-Z0-9_\-]{1,63}(?<!-)\.)+(?:[a-zA-Z]{2,})$)', re.IGNORECASE)
	regex = re.compile(r'[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,5}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?|'
		r'(([2]([0-4][0-9]|[5][0-5])|[0-1]?[0-9]?[0-9])[.]){3}(([2]([0-4][0-9]|[5][0-5])|[0-1]?[0-9]?[0-9]))', re.IGNORECASE)

	if regex.match(name):
		return True
	else:
		return False

def isURLValid(url) :
	#regex = re.compile(
		#r'^(?:http|ftp)s?://' # http:// or https://
		#r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
		#r'localhost|' #localhost...
		#r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
		#r'(?::\d+)?' # optional port
		#r'(?:/?|[/?]\S+)$', re.IGNORECASE)	
	regex = re.compile(
        r'^(?:[a-z0-9\.\-]*)://'  # scheme is validated separately
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}(?<!-)\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)        
	if regex.match(url):
		return True
	else:
		return False
   
def isPathValid(strg, search=re.compile(r'^\/[/.a-zA-Z0-9-~_+:%=;,!]*$').search):
	return bool(search(strg))    


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
	global valid_urls,invalid_urls, fixed_url_counter
	schemes = ['http', 'https']
	
	for url in lines:
		url = url.strip()		
		if not url.startswith('#') :
			parsed_url = urlparse(url)
			if parsed_url.scheme not in schemes:
				#print "Found url missing protocol sheme, fixing it..."
				new_url = "http://" + url
				valid_urls[new_url] = 'FIXED'
				#parse again the URL
				parsed_url = urlparse(new_url)
				fixed_url_counter+=1
			elif isURLValid(url) and isDomainNameValid(parsed_url.netloc):
				valid_urls[url] = ''
			else:
				invalid_urls[url] = 'MALFORMED'


def search(args):
	global fixed_url_counter
	print "Input file: " + args.source_file[0]
	print "Output file: " + args.dest_file[0]
	print "Invalid url's file: " + args.invalid_file[0] + "\n"
	print "Parsing url's...\n"
	
	#Step 1: Load the file and split valid lines from malformed ones
	parseFile(args.source_file[0])
	print "Number of valid url's: " + `len(valid_urls)`
	#TODO # of fixed urls
	print "Number of malformed url's: " + `len(invalid_urls)`
	print "Number of fixed url's: " + `fixed_url_counter`
	#Step 2: Test valid url's and split the invalid ones (anything that)
	#doesn't returns a HTTP 200 ok code.
	print "\nTesting valid url's..."
	testUrls()
	print "Done."
	
	print "Writing results to output files...\n"
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
		      help='Path to file containing url\'s to validate.', 
		      required=True)
  parser.add_argument('-d', '--dest', 
		      dest='dest_file', 
		      nargs=1, 
		      help='Name of file containing the list of valid url\'s.',
		      required=True)
  parser.add_argument('-i', '--invalid', 
		      dest='invalid_file', 
		      nargs=1, 
		      help='Name of file containing the list of invalid url\'s.', 
		      required=True)  
  parser.add_argument('--verbose', '-v', 
		      action='count', 
		      help='Verbose output.')
  parser.add_argument('--version', action='version', version='urlvalidator 0.1 \n')		    

  parser.set_defaults(func=search)
  args = parser.parse_args()
  args.func(args)

if __name__ == "__main__":
  run()