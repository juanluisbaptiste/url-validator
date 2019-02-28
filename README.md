# URL Validator

Validate a list of URL's and save the results into a file.

Options:

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



## License

This project is licensed under the GPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
