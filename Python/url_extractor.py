## Simple URL Extractor
## ToUse, at CLI $> python3 main.py [Replace With URL No Braces]
## Will output a list of all href links on a page to a file witht he date time and URL.
## Useful for pushing to a bulk downloader program, though it does not processing so URLs may need to be edited
## If there is not full URL, it pre prends an easily find/replaceable slug

import httplib2
import sys
from datetime import datetime
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urljoin

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

try:
    url = sys.argv[1]
except IndexError:
    print("Error: No URL Defined! Please use main.py [URL]")
    sys.exit(1)

http = httplib2.Http()
status, response = http.request(url)
filename = f"{current_datetime}-{url.split('//')[1].replace('/','_')}-images.txt"

with open(filename, "x") as f:
    for link in BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            #print(link['href'])
            write_link = link['href']
            if "http://" not in write_link:
                write_link = f"REPLACEME_{write_link}"
            f.write(f"{write_link}\n")
## Reference
## https://stackoverflow.com/questions/1080411/retrieve-links-from-web-page-using-python-and-beautifulsoup
## https://stackoverflow.com/questions/4033723/how-do-i-access-command-line-arguments
## https://stackoverflow.com/questions/14016742/detect-and-print-if-no-command-line-argument-is-provided
