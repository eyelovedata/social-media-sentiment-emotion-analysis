import sqlite3
import sys
import urllib
import urllib.request
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# INSERT YOUR DATABASE NAME HERE
conn = sqlite3.connect('<YOUR DATABASE>')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS Terms (id INTEGER PRIMARY KEY, term TEXT UNIQUE)''')
cur.execute('''CREATE TABLE IF NOT EXISTS Threads (id INTEGER PRIMARY KEY, forum TEXT, url TEXT UNIQUE, html TEXT, terms_id INTEGER, title TEXT, FOREIGN KEY(terms_id) REFERENCES Terms(id))''')

errored = []


BASE_URL = 'http://www.medhelp.org/'
DECORATED_URL = BASE_URL + 'search/expanded?cat=posts&page=PAGE&'
SEARCH_TERM = input('Enter your search term - ')


def insert_search_term():
    if (len(SEARCH_TERM) < 1):
        print('The search term you inputted is invalid.')
        quit()
    cur.execute('INSERT OR IGNORE INTO Terms (term) VALUES ( ? )', (SEARCH_TERM, ))
    conn.commit()


def upsert_thread_info():
    page = 1
    search_url = DECORATED_URL + urllib.parse.urlencode({'query': SEARCH_TERM})
    cur.execute('SELECT id FROM Terms WHERE term = ? ', (SEARCH_TERM, ))
    TERMS_ID = cur.fetchone()[0]
    print('Getting the url, forum and title for each thread...')

    while True:
        try: 
            url = search_url.replace('PAGE', str(page))
            req = urllib.request.Request(url,
                data=None,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                }
            )
            html = urllib.request.urlopen(req).read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            thread_anchors = soup.select('div.section_content div div.result div.mh_info span.title a')
            if(len(thread_anchors) == 0):
                print('No more threads to extract. Terminating thread information extraction.')
                break
            print('Retrieving thread urls, forums and titles from page', page, '...')
            for thread_anchor in thread_anchors:
                href = thread_anchor.get('href')
                thread_url = (urljoin(BASE_URL, href))
                title = thread_anchor.get_text(strip=True)
                forum = thread_url.split('/')[-4]
                cur.execute('INSERT OR IGNORE INTO Threads (url, forum, title, terms_id) VALUES (?, ?, ?, ?)', (thread_url, forum, title, TERMS_ID))
                conn.commit()
        except Exception as e:
            errored.append(['Threads url and info extraction on page', page, 'at', url, ':', e])
            print('Error on page', page, 'at ', url, ':', e)
        page += 1


def upsert_thread_html():
    for row in conn.execute('SELECT id, url FROM Threads WHERE html is NULL'):
        try:
            threads_id = row[0]
            if threads_id % 25 == 0:
                print('Fetching HTML for thread...', threads_id)
            url = row[1]
            req = urllib.request.Request(
                url,
                data=None,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                }
            )
            html = urllib.request.urlopen(req).read().decode('utf-8')
            cur.execute('UPDATE Threads SET html=? WHERE url=?', (str(html), url))
        except Exception as e:
            threads_id = row[0]
            url = row[1]
            errored.append(['Threads html extraction: ', 'thread id', threads_id, 'at', url, ':', e])
            print('Could not get HTML from thread ', threads_id, 'found at', url, ':', e)
        conn.commit()


insert_search_term()
print('Your thread extraction is beginning...')
upsert_thread_info()
print('Your html extraction for each thread is beginning...')
upsert_thread_html()
print('Your thread exctraction is complete. The following have failed:', errored)

