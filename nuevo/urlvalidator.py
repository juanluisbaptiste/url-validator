#!/usr/bin/python
import argparse
import os
import re
import sys
from urlparse import urlparse
import itertools
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.ioloop

concurrent = 200
finished=itertools.count(1)
added=0
original_urls = None
valid_urls = {}
valid_urls_counter = 0
invalid_urls = {}
url_counter = 0
fixed_url_counter = 0
processed_urls_counter = 0

def isDomainNameValid ( name ):
    # TODO: Works but accepts hostnames with a name of at least 3 characters with no domain. ie. www instead of www.test.com
    regex = re.compile(r'[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,5}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?|'
        r'(([2]([0-4][0-9]|[5][0-5])|[0-1]?[0-9]?[0-9])[.]){3}(([2]([0-4][0-9]|[5][0-5])|[0-1]?[0-9]?[0-9]))', re.IGNORECASE)

    if regex.match(name):
        return True
    else:
        return False

def isURLValid(url) :
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
    global concurrent
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    http_client = AsyncHTTPClient(max_clients=concurrent)
    for url in valid_urls:
        request = HTTPRequest(url,method="HEAD",
                              body=None, 
#                             request_timeout = 10.0,
#                             connect_timeout = 10.0,
#                             follow_redirects=self._follow_redirects,                              
                              validate_cert=False)
        http_client.fetch(request, handle_request)
    tornado.ioloop.IOLoop.instance().start() # start the tornado ioloop to listen for events

def handle_request(response):
    global url_counter, processed_urls_counter, valid_urls_counter
    if response.error:
        invalid_urls[response.request.url] = response.error
        #Found an url with a connection error, remove it from the valid list    
        del valid_urls[response.request.url]

    else:
        #if the code is any of these valid ones add the url and code to 
        #valid_urls
        if response.code < 400:
            valid_urls[response.request.url] = response.code
        else :
            #else add it to invalid_urls
            invalid_urls[response.request.url] = response.reason
            del valid_urls[response.request.url]
    processed_urls_counter += 1
    print "Processed url " + `processed_urls_counter` + " of " + `valid_urls_counter` + " " + response.request.url      
    if (processed_urls_counter >= len(valid_urls)):
        print "Found " + `valid_urls_counter - processed_urls_counter` + " invalid url's"
        print "Finishing off...\n"        
        tornado.ioloop.IOLoop.instance().stop()

def writeInvalidFile(filename):
    global invalid_urls
    content=""

    for url in invalid_urls:
        content += url + "," + `invalid_urls[url]` + "\n"
    saveFile(filename, content)

def writeValidFile(filename):
    global valid_urls
    content=""

    for url in valid_urls:
        content += url + "," + `valid_urls[url]` + "\n"
    saveFile(filename, content)

def parseFile(filename):
    global url_counter,original_urls ,invalid_urls, fixed_url_counter, valid_urls_counter
    original_urls = openFile(filename)
    schemes = ['http', 'https']
    
    for url in original_urls:
        url = url.strip()
        if not url.startswith('#') : #The line isn't commented
            url_counter += 1
            parsed_url = urlparse(url)

            if not parsed_url.path.startswith('/'):
                path = parsed_url.path + "/"
            else:
                path = parsed_url.path

            #First test to see if the url is valid
            if isURLValid(url) and isDomainNameValid(parsed_url.netloc) and isPathValid(path):
                #Add it to valid_urls, it doesn't matter to put something here.
                valid_urls[url] = ''
                #If the url is missing the HTTP protocol, add it as http
            elif parsed_url.scheme not in schemes:
                #TODO: Try to fix white spaces in path
                url = "http://" + url
                #parse again the URL
                parsed_url = urlparse(url)

                #test the url again
                if isDomainNameValid(parsed_url.netloc):
                    fixed_url_counter+=1
                    valid_urls[url] = 'FIXED'
                else:
                    invalid_urls[url] = 'MALFORMED_PATH_DOMAIN'
            else:
                invalid_urls[url] = 'MALFORMED_URL'
        valid_urls_counter = len(valid_urls)


def search(args):
    global url_counter,fixed_url_counter, concurrent

    #Set cli parameter for concurrent connections
    if args.concurrent_conn > 0 :
        if args.test_urls :
            concurrent = int(args.concurrent_conn[0])
        else:
            print "ERROR: concurrent --concurrent-connections (-c) parameter can only be used with --test-urls (-t) parameter"
            sys.exit(1)

    print "Input file: " + args.source_file[0]
    print "Output file: " + args.dest_file[0]
    print "Invalid url's file: " + args.invalid_file[0] + "\n"

    #Step 1: Load the file and split valid lines from malformed ones
    parseFile(args.source_file[0])
    print "Parsing a total of " + `url_counter` + " url's...\n"
    print "Number of non-malformed url's: " + `len(valid_urls)`
    print "Number of fixed url's: " + `fixed_url_counter`
    print "Number of malformed url's: " + `len(invalid_urls)`
    print "Number of duplicated url's: " + `url_counter - len(valid_urls) - len(invalid_urls)`

    if args.test_urls:
        #Step 2: Test valid url's and split the invalid ones (anything that)
        #doesn't returns a HTTP 200, 301 or 302 HTTP codes.
        print "Testing valid url's (this can take a while)..."
        print "Concurrent connections: " + str(concurrent)

        testUrls()
        print "Done."
        print "Found " + `valid_urls_counter - processed_urls_counter` + " invalid url's"
        print "\nResults:\n"
        print "Number of valid url's: " + `len(valid_urls)`
        print "Number of invalid url's: " + `len(invalid_urls)`
        print "\nWriting results to output files..."
    print "\nTotal of parsed url's: " + `len(valid_urls) + len(invalid_urls)` + "\n"
        
    #Step 3: Save new lists to their respective files
    writeInvalidFile(args.invalid_file[0])
    writeValidFile(args.dest_file[0])


def run():
    global concurrent
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
    parser.add_argument('-t', '--test-urls',
              #dest='test_urls',
              action='store_true',
              help='Try to connect to valid url\'s to discard the ones with connection problems (timeouts, dns failure, 404 errors, etc).',
              required=False)
    parser.add_argument('-c', '--concurrent-connections',
              dest='concurrent_conn',
              nargs=1,
              help='Amount of concurrent connections to launch (default is ' + `concurrent` + ').',
              required=False)
    parser.add_argument('--verbose', '-v',
              action='count',
              help='Verbose output.')
    parser.add_argument('--version', action='version', version='urlvalidator 0.1 \n')

    parser.set_defaults(func=search)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    run()
