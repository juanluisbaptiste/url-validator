# URL Validator

Validate a list of url's and save the results into a CSV file.

I developed this tool for work some time ago. At the time, we periodically
received from a partner a file with a list of url's that we needed to be
loaded in some software. The problem was that some of the url's in the file
came with syntax errors, or were non-existent or non-accessible ones. So we needed to validate the contents of the file, try to fix the url's with syntax errors, and split the invalid ones from the good ones in two separate files.

Nowadays I use it to validate my [OneTab](https://www.one-tab.com/) url list
from time to time.

## Getting Started

This is the full list of options:


```
usage: urlvalidator.py [-h] -s SOURCE_FILE -d DEST_FILE -i INVALID_FILE [-t]
                       [-c CONCURRENT_CONN] [--verbose] [--version]

URL Validator Tool.

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE_FILE, --source SOURCE_FILE
                        Path to file containing url's to validate.
  -d DEST_FILE, --dest DEST_FILE
                        Name of file to save the list of valid url's.
  -i INVALID_FILE, --invalid INVALID_FILE
                        Name of file to save the list of invalid url's.
  -t, --test-urls       Try to connect to valid url's to discard the ones with
                        errors (timeouts, dns failure, HTTP errors >= 400 ,
                        etc).
  -c CONCURRENT_CONN, --concurrent-connections CONCURRENT_CONN
                        Amount of concurrent connections to launch (default is
                        200).
  --verbose, -v         Verbose output.
  --version             show program's version number and exit
```

For example, use the included example file [tests_files](test_files/urls.txt). To test it only for syntax errors:

```
python urlvalidator.py -s test_files/urls.txt -d valids.txt -i invalids.txt
```

To also invoke them to test if they are valid url's (they return a 200 HTTP code) add the `-t` option:

```
python urlvalidator.py -s test_files/urls.txt -d valids.txt -i invalids.txt -t
```

### Prerequisites

What things you need to install the software and how to install them

- Python 2.7.x
- Python Tornado library

## License

This project is licensed under the GPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
