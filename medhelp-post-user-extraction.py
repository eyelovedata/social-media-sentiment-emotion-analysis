import sqlite3
import sys
import urllib.request as urllib
from bs4 import BeautifulSoup
from datetime import datetime
import re

# INSERT YOUR DATABASE NAME HERE
conn = sqlite3.connect('<YOUR DATABASE>')
c = conn.cursor()
c2 = conn.cursor()

c2.execute('''CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, doctor INTEGER, profile_url TEXT, profile_html TEXT, age INTEGER, sex TEXT, member_since DATETIME, location TEXT, marker INTEGER)''')
c2.execute('''CREATE TABLE IF NOT EXISTS Posts (id INTEGER PRIMARY KEY, users_id INTEGER, threads_id INTEGER, number INTEGER, content TEXT UNIQUE, date DATETIME, label TEXT, sent_score FLOAT, anger_score FLOAT, sadness_score FLOAT, fear_score FLOAT, disgust_score FLOAT, joy_score FLOAT, marker INTEGER, FOREIGN KEY(users_id) REFERENCES Users(id), FOREIGN KEY(threads_id) REFERENCES Threads(id))''')

errored = []


def upsert_user(user):
    try:
        username = user.text.strip()
        profile_url = 'http://www.medhelp.org' + str(user.find('a')['href']) + '/'
        req = urllib.Request(profile_url)
        req.add_header('User-agent', 'Mozilla 5.10')
        document = urllib.urlopen(req)
        _profile_html = document.read()
        profile_html = str(_profile_html)
        profile_html_soup = BeautifulSoup(_profile_html, 'html.parser')
        doctor = 1 if 'doctor_profile' in profile_html else 0

        if doctor == 1:
            doctor_gender = get_doctor_gender(profile_html)
            doctor_summary_info = profile_html_soup.find('div', class_='doctor_summary_info')
            doctor_age = get_doctor_age(doctor_summary_info)
            doctor_location = get_doctor_location(profile_html_soup)
            c2.execute('INSERT OR IGNORE INTO Users (username, doctor, profile_url, profile_html, age, sex, member_since, location, marker) VALUES(?,?,?,?,?,?,?,?,?)', (username, doctor, profile_url, profile_html, doctor_age, doctor_gender, None, doctor_location, 1))
        else:
            member_since = get_member_since(profile_html)
            member_about_me = profile_html_soup.select('div.section span ')
            member_age = get_member_age(member_about_me)
            member_gender = get_member_gender(member_about_me)
            member_location = get_member_location(member_about_me)
            c2.execute('INSERT OR IGNORE INTO Users (username, doctor, profile_url, profile_html, age, sex, member_since, location, marker) VALUES (?,?,?,?,?,?,?,?,?)', (username, None, profile_url, profile_html, member_age, member_gender, member_since, member_location, 1))

    except Exception as e:
        print('Failed to get profile for ', username, 'at', profile_url, ':', e)
        errored.append(['User extraction for username', username, 'at', profile_url, ':', e])
        c2.execute('INSERT OR IGNORE INTO Users (username,  profile_url) VALUES (?,?)', (username, profile_url))
    return c2.execute('SELECT id FROM Users WHERE username = ?', (username,)).fetchone()[0]


def get_date_list(html_soup, raw_html):
    date_list = list()
    unix_date_list = html_soup.select('.mh_timestamp')
    if not unix_date_list:
        string_date_list = re.findall(r'([A-Z][a-z]{2} \d{1,2}, \d{4})', str(raw_html))
        for element in string_date_list:
            date = datetime.strptime(element, '%b %d, %Y')
            date_list.append(date)

    for element in unix_date_list:
        unix_date = element.get('data-timestamp')
        date = datetime.fromtimestamp(float(unix_date))
        date_list.append(date)
    return date_list


def get_doctor_age(doctor_summary_info_list):
    doctor_age_list = re.findall(r', (\d{2})', str(doctor_summary_info_list))
    if len(doctor_age_list) > 0:
        return doctor_age_list[0]


def get_doctor_gender(profile_html):
    if 'Male' in profile_html:
        return 'Male'
    elif 'Female' in profile_html:
        return 'Female'
    else:
        return


def get_doctor_location(profile_html_soup):
    doctor_location_list = profile_html_soup.select('div.contact_info_box div.value')
    if len(doctor_location_list) > 0:
        return doctor_location_list[0].get_text()

    doctor_summary_info = profile_html_soup.select('span.doctor_name')[0]
    doctor_summary_info.extract()
    doctor_summary_info = str(profile_html_soup.select('div.doctor_summary_info')[0])
    doctor_location_list = re.findall(r'[a-zA-Z]+,\s[a-zA-Z]+', doctor_summary_info)
    if len(doctor_location_list) > 0:
        return doctor_location_list[0]


def get_member_since(profile_html):
    member_since = re.findall(r'member since ([A-Z][a-z]{2} \d{4})', profile_html)
    if len(member_since) > 0:
        return datetime.strptime(member_since[0], '%b %Y')


def get_member_age(about_me_list):
    if len(about_me_list) > 1:
        age_list = re.findall(r', (\d{1,2})', about_me_list[1].get_text())
        if len(age_list) > 0:
            return age_list[0]


def get_member_gender(about_me_list):
    if len(about_me_list) > 1:
        gender = about_me_list[1].get_text()
        if 'Female' in gender:
            return 'Female'
        elif 'Male' in gender:
            return 'Male'


def get_member_location(about_me_list):
    if len(about_me_list) > 3:
        if str(about_me_list[2]).startswith('<span>'):
            return about_me_list[2].get_text()


c.execute('SELECT html, id FROM Threads')
threads_processed = 1
print('Your post and user extraction has begun.')
for row in c:
    if (threads_processed % 10 == 0):
        print('Retrieving post and user information for thread', threads_processed, '...')
    raw_html = row[0]
    threads_id = row[1]
    try:
        html_soup = BeautifulSoup(raw_html, 'html.parser')
    except Exception as e:
        errored.append(['Threads parsing for threads_id', threads_id])
        print('Failed to parse html for thread id', threads_id, ':', e)

    response_list = html_soup.select('.subj_body > #subject_msg, .resp_body')
    user_list = html_soup.select('.username')
    date_list = get_date_list(html_soup, raw_html)
    response_num = 0
    for index, response in enumerate(response_list):
        try:
            date = date_list[index]
            content = response.get_text()
            username = user_list[index].text.strip()
            c2.execute('SELECT id FROM Users WHERE username = ?', (username,))
            users_id = c2.fetchone()
            if users_id is None:
                users_id = upsert_user(user_list[index])
            else:
                users_id = users_id[0]
            c2.execute('INSERT or IGNORE INTO Posts (threads_id, content, \
                       number, date, users_id) VALUES (?,?,?,?,?)',
                       (threads_id, content, response_num, date, users_id))
            c2.execute('SELECT id FROM Posts WHERE content= ?', (content,))
            posts_id = c2.fetchone()[0]
            response_num += 1
        except Exception as e:
            print('Failed to process post id', posts_id, ':', e)
            errored.append(['Posts processing for post id', posts_id, 'of thread id', threads_id, 'corresponding to user list', user_list[index]])
    threads_processed = threads_processed + 1
    conn.commit()

print('Your post and user extraction is complete. Errors:', errored)
