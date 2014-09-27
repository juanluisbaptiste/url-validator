#!/usr/bin/python
import argparse
import os
import re
import sys
from urlparse import urlparse

BAD_URL=0
CODE_200=1
CODE_404=2
CODE_500=3


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
        arch = open(filename, 'aw')
        try:
            arch.write(content + '\r\n')
        finally:	
            arch.close()


def writeInvalidFile(filename,invalidLines,code):
	content=""
	
	for i in invalidLines:
		content += i + "," + `code` + "\r\n"
	saveFile(filename, content)

def writeValidFile(filename,validLines):
	content=""
	
	for i in validLines:
		content += i + "\r\n"
	saveFile(filename, content)
	
	
def parseFile(filename, validLines, invalidLines):
	lines = openFile(filename)
	
	for i in lines:
		i = i.strip()
		if not isURLValid(i):
			if not isDomainNameValid(i):
				#print "INVALID URL: " + i
				invalidLines.append(i)
			else:
				url = urlparse(i)
				if not url.scheme == "http" :
					i = "http://" + i					
				if not url.scheme == "https" :
					i = "https://" + i
				validLines.append(i)
		else:
			#print "VALID URL=" + i
			validLines.append(i)

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

    #Save new lists to their respective files
	writeInvalidFile(args.invalid_file[0], invalidLines, BAD_URL)
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