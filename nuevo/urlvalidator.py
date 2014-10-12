#!/usr/bin/python
"""
URL validation tool. 
It receives a file with url's to discard malformed url's 
from valid ones.

If the --test-urls parameter is specified then the non-malformed
url's will be tested to see if they don't have any connection 
errors or return HTTP error codes.
"""
import argparse
import os
import re
import sys
from urlparse import urlparse
import itertools
import signal 
import sys
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import tornado.ioloop

request_timeout = HTTPRequest._DEFAULTS["request_timeout"]
connect_timeout = HTTPRequest._DEFAULTS["connect_timeout"]
concurrent = 200
request = None
finished=itertools.count(1)
original_urls = None
valid_urls = {}
valid_urls_counter = 0
invalid_urls = {}
invalid_urls_counter = 0
url_counter = 0
fixed_url_counter = 0
processed_urls_counter = 0
verboseprint = None

def signal_handler(signal, frame):
    """
    Ctr-C signal handler function to be able to stop
    a running test.

    Parameters
    ----------

    signal : signal
        The signal the process received.
    frame : handler
        function to call when the signal is received to 
        process it.
    """
    print "\nUser pressed Ctrl-C, stopping..."
    stopTest()
    sys.exit(0)
#Connects the SIGINT signal to our handler function to process it    
signal.signal(signal.SIGINT, signal_handler)
    
def isDomainNameValid ( name ):
    """
    Checks if a domain name is valid (ie: www.python.org)

    Parameters
    ----------

    name : string 
        Domain to verify

    Returns
    -------
    bool
        Returns True if the domain matches the regex 
        (is valid), False otherwise.

    """
    # TODO: Works but accepts hostnames with a name of at least 3 characters with no domain. ie. www instead of www.test.com
    regex = re.compile(r'[-a-zA-Z0-9@:%_\+.~#?&//=]{2,256}\.[a-z]{2,5}\b(\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?|'
        r'(([2]([0-4][0-9]|[5][0-5])|[0-1]?[0-9]?[0-9])[.]){3}(([2]([0-4][0-9]|[5][0-5])|[0-1]?[0-9]?[0-9]))', re.IGNORECASE)

    if regex.match(name):
        return True
    else:
        return False

def isURLValid(url) :
    """
    Checks if a URL is valid (ie: http://www.python.org/doc/)

    Parameters
    ----------

    url : string 
        URL to verify

    Returns
    -------
    bool
        Returns True if the url matches the regex 
        (is valid), False otherwise.

    """
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

def isPathValid(strg, start=re.compile(r'^\/[/.a-zA-Z0-9-~_+:%=;,!]*$').search):
    """
    Checks if the path part of an url is valid (ie: /foo)

    Parameters
    ----------

    strg : string 
        URL path to verify
    start : regex 
        Regular expression to use to test the path
    Returns
    -------
    bool
        Returns True if the path matches the regex 
        (is valid), False otherwise.

    """
    return bool(start(strg))


def openFile(filename, mode = 'r'):
    """
    Opens a file. 

    Parameters
    ----------

    filename : string 
        Path to the file to open.    
    mode : string
        mode to open the file, read-only by default.

    Returns
    -------
    Array_like
        Returns the file contents.

    """
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
    """
    Saves a file. 

    Parameters
    ----------

    filename : string 
        Path to the file to save.    
    mode : string
        Contents to save to the file.

    """
    arch = open(filename, 'w')
    try:
        arch.write(content)
    finally:
        arch.close()

def testUrls():
    """
    Connects to each of the non-malformed url's to see if they are 
    valid. Valid means we can connect to them and they return a 
    HTTP code < 400. Any other type of error (DNS failure, connect 
    timeout, HTTP codes >= 400) will move the url to the 
    invalids list.

    The connections are done asynchronically using the Tornado library.
    """    
    global concurrent, request_timeout, connect_timeout, request
    #Use the curl implementation for better performance

    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    http_client = AsyncHTTPClient(max_clients=concurrent)

    for url in valid_urls:
        request = HTTPRequest(url,method="HEAD",
                              body=None, 
                             request_timeout = request_timeout,
                             connect_timeout = connect_timeout,
                              validate_cert=False)
        http_client.fetch(request, handle_request)
    tornado.ioloop.IOLoop.instance().start() # start the tornado ioloop to listen for events


def stopTest():
    """
    Stop the tornado IOLoop to finish the tests.

    Returns
    -------
    bool
        Returns True if the loop was stopped successfully, 
        False otherwise.
    """
    verboseprint("Finishing off...\n")
    return tornado.ioloop.IOLoop.instance().stop()

def handle_request(response):
    """
    Handles an HTTP response from one of the async 
    connections. 

    Parameters
    ----------

    response : HTTPResponse 
        HTTP response object.    
    
    """    
    global url_counter, processed_urls_counter, valid_urls_counter, invalid_urls_counter

    #Handle error responses (DNS failures, timeouts, etc)
    if response.error:
        invalid_urls[response.request.url] = `response.code` + " - " + response.reason
        #Found an url with a connection error, remove it from the valid list    
        del valid_urls[response.request.url]
        invalid_urls_counter += 1
    else:
        #if the code is any of these valid ones add the url and code to 
        #valid_urls
        if response.code < 400:
            valid_urls[response.request.url] = response.code
        else :
            #else add it to invalid_urls
            invalid_urls[response.request.url] = response.reason
            del valid_urls[response.request.url]
            invalid_urls_counter += 1

    #Count this url as processed
    processed_urls_counter += 1
    verboseprint("Processed url " + `processed_urls_counter` + " of " + `valid_urls_counter` + " " + response.request.url)
    #If all urls have been processed, stop the IOLoop
    if (processed_urls_counter == valid_urls_counter):
        stopTest()

def writeInvalidFile(filename):
    """
    Saves the file with the invalid url's. 

    Parameters
    ----------

    filename : string 
        Path to the file to save.

    """    
    global invalid_urls
    content=""

    for url in invalid_urls:
        content += url + "," + `invalid_urls[url]` + "\n"
    saveFile(filename, content)

def writeValidFile(filename):
    """
    Saves the file with the valid url's. 

    Parameters
    ----------

    filename : string 
        Path to the file to save.    

    """    
    global valid_urls
    content=""

    for url in valid_urls:
        content += url + "," + `valid_urls[url]` + "\n"
    saveFile(filename, content)

def parseFile(filename):
    """
    Parses the input file separating the malformed url's 
    from the non-malformed ones. 

    Parameters
    ----------

    filename : string 
        Path to the file to open.    

    """    
    global url_counter,original_urls ,invalid_urls, fixed_url_counter, valid_urls_counter, invalid_urls_counter
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
        invalid_urls_counter = len(invalid_urls)


def start(args):
    """
    Starts the validation process. First it will look 
    for malformed url's. Then, if the --test-urls 
    parameter is used it will try to connect to each of 
    the valid url's and mark as invalid the ones with
    errors.  

    Parameters
    ----------

    args : *args 
        Command line parameters    

    """
    global url_counter,fixed_url_counter, concurrent, verboseprint, invalid_urls_counter

    if args.verbose:
        def _verboseprint(*args):
            # Print each argument separately so caller doesn't need to
            # stuff everything to be printed into a single string
            for arg in args:
                print arg,
            print
    else:   
        _verboseprint = lambda *a: None  
    verboseprint = _verboseprint    

    #Set cli parameter for concurrent connections
    if args.concurrent_conn > 0 :
        if args.test_urls :
            concurrent = int(args.concurrent_conn[0])
        else:
            print "ERROR: concurrent --concurrent-connections (-c) parameter can only be used with --test-urls (-t) parameter"
            sys.exit(1)

    #Step 1: Load the file and split valid lines from malformed ones
    parseFile(args.source_file[0])
    parsingFileStats(args)

    if args.test_urls:
        #Step 2: Test valid url's and split the invalid ones (anything that)
        #doesn't returns a HTTP 200, 301 or 302 HTTP codes.
        print "\nTesting valid url's (this can take a while)..."
        verboseprint("Concurrent connections: " + str(concurrent) + "\n")
        #reset invalid urls counter to count for urls with errors
        invalid_urls_counter = 0
        testUrls()
        print "Done."
        testUrlsStats()
    print "Total of parsed url's: " + `len(valid_urls) + len(invalid_urls)`
        
    #Step 3: Save new lists to their respective files
    verboseprint("\nWriting results to output files...")
    writeInvalidFile(args.invalid_file[0])
    writeValidFile(args.dest_file[0])

def parsingFileStats(args):
    """
    Prints some stats about the results found after 
    parsing the file contents looking for malformed 
    url's.

    Parameters
    ----------

    args : *args 
        Command line parameters    

    """
    print "Input file: " + args.source_file[0]
    print "Output file: " + args.dest_file[0]
    print "Invalid url's file: " + args.invalid_file[0] + "\n"
    print "Parsing a total of " + `url_counter` + " url's...\n"
    print "Non-malformed url's: " + `len(valid_urls)`
    print "Fixed url's: " + `fixed_url_counter`
    print "Malformed url's: " + `invalid_urls_counter`
    print "Duplicated url's: " + `url_counter - len(valid_urls) - len(invalid_urls)`


def testUrlsStats():
    """
    Prints some stats about the results found after 
    testing all of the non-malformed url's looking 
    for errors.

    """
    print "\nFound " + `invalid_urls_counter` + " invalid url's"
    print "\nResults:\n"
    print "Valid url's: " + `len(valid_urls)`
    print "Total invalid url's: " + `len(invalid_urls)`

def run():
    """
    Main function, handles the command line parameters 
    and calls the start() function to process them and 
    start the tests.
    """
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
              help='Name of file to save the list of valid url\'s.',
              required=True)
    parser.add_argument('-i', '--invalid',
              dest='invalid_file',
              nargs=1,
              help='Name of file to save the list of invalid url\'s.',
              required=True)
    parser.add_argument('-t', '--test-urls',
              #dest='test_urls',
              action='store_true',
              help='Try to connect to valid url\'s to discard the ones with errors (timeouts, dns failure, HTTP errors >= 400 , etc).',
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

    parser.set_defaults(func=start)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    run()
