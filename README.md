# Daily Coding Problem - Downloader
Daily Coding Problem is a very good service that send coding problems for you to solve on a daily basis. 
The problems are sent on one day while the solution is sent on the next day along with the next problem.
While this is great, since the problems comes via email, it is lost in your inbox and you have to navigate
to the DCP website in order to see the solutions. 

This downloaders helps with that by reading all mails from DCP on your gmail and then navigating to the
DCP website in order to build a neat offline repository of problems + solutions. 

Note: Don't re-distribute the downloaded solutions. It is for personal use only.
DCP is providing a paid service and I would encourage those that are interested to go and subscribe to 
Daily Coding Problem if you like the content they provide. 

## How to run
The solution is built on Python3 and uses a GMail API key to read the emails.

1. Install the project dependencies
`$ pip install -r requirements.txt`

2. Enable the GMail API on GCP
Follow the guide (here)[https://developers.google.com/gmail/api/quickstart/python]

3. Download the credentials json and save it into the `config` folder

5. Run the following programs\
    a. Download the list of emails\
    `$ python download_emails.py`\
    b. Download the list of links from the emails\
    `$ python download_links.py`\
    c. Download the solution content from the links\
    `$ python download_solutions.py`

Commands in Step 5 can be run iteratively and independently to fetch new content.

The `check*`, `add*` files can be used to look for data issues and rectify manually.


