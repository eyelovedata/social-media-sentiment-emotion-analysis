import json
import sqlite3
import sys
import logging

import requests
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import (EmotionOptions,
                                                          Features,
                                                          KeywordsOptions,
                                                          SentimentOptions)

conn = sqlite3.connect("<DB_NAME>.sqlite")
conn.text_factory = str
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS keywords (id INTEGER PRIMARY KEY, name TEXT, UNIQUE (name))''')
cur.execute('''CREATE TABLE IF NOT EXISTS keyword_sent_scores (PRIMARY KEY (posts_id, keywords_id), posts_id INTEGER, keywords_id INTEGER, sent_score FLOAT, relevance FLOAT, sadness_score FLOAT, joy_score FLOAT, fear_score FLOAT, disgust_score FLOAT, anger_score FLOAT)''')
cur.execute('''CREATE TABLE IF NOT EXISTS sent_raw (posts_id INTEGER, raw_result TEXT)''')

authenticator = IAMAuthenticator("<API_KEY>")
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version="2019-07-12", authenticator=authenticator
)

natural_language_understanding.set_service_url(
    "<SERVICE_URL>"
)

cur.execute(
    """SELECT id, content FROM posts WHERE marker is not 1 ORDER BY id"""
)

for row in c:
    posts_id = row[0]
    post_content = row[1]
    if posts_id % 10 == 0:
        logging.info("Performing sentiment analysis for post id", posts_id)

        try:
            f = Features(
                keywords=KeywordsOptions(sentiment=True, emotion=True),
                sentiment=SentimentOptions(document=True),
                emotion=EmotionOptions(document=True)
            )
            r = natural_language_understanding.analyze(
                text=post_content, features=f, language="en"
            ).get_result()

            results_ser = json.dumps(r)
            results = json.loads(results_ser)
            cur.execute(
                "INSERT INTO sent_raw (posts_id, raw_result) VALUES (?,?)",
                (posts_id, results_ser),
            )
        except Exception as e:
            logging.warning("Error on post id", posts_id, e)
            cur.execute("UPDATE Posts SET marker=0 WHERE id = ?", (posts_id,))
            continue

        try:
            label = results["sentiment"]["document"]["label"]
            sent_score = results["sentiment"]["document"]["score"]
            anger_score = results["emotion"]["document"]["emotion"]["anger"]
            sadness_score = results["emotion"]["document"]["emotion"]["sadness"]
            joy_score = results["emotion"]["document"]["emotion"]["joy"]
            fear_score = results["emotion"]["document"]["emotion"]["fear"]
            disgust_score = results["emotion"]["document"]["emotion"]["disgust"]
            cur.execute(
                "UPDATE Posts SET sent_score = ?, label = ?, anger_score = ?, sadness_score = ?, joy_score = ?, fear_score = ?, disgust_score = ? WHERE id = ? ", (sent_score, label, anger_score, sadness_score, joy_score, fear_score, disgust_score, posts_id)
            )
        except Exception as e:
            logging.warning("Error inserting post scores for post id", posts_id, e)
            continue

        keyword_list = results["keywords"]
        for keyword in keyword_list:
            try: 
                name = keyword["text"]
                cur.execute(
                    "INSERT or IGNORE INTO keywords (name) VALUES (?)",
                    (name,),
                )
                cur.execute(
                    "SELECT id FROM Keywords WHERE name = ?", (name,)
                )

                keywords_id = cur.fetchall()[0][0]
                sent_score = keyword["sentiment"]["score"]
                relevance = keyword["relevance"]
                sadness_score = keyword["emotion"]["sadness"]
                joy_score = keyword["emotion"]["joy"]
                fear_score = keyword["emotion"]["fear"]
                disgust_score = keyword["emotion"]["disgust"]
                anger_score = keyword["emotion"]["anger"]
                cur.execute(
                    "INSERT OR IGNORE INTO keyword_sent_scores (posts_id, keywords_id, sent_score, relevance, sadness_score, joy_score, fear_score, disgust_score, anger_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (posts_id, keywords_id, sent_score, relevance, sadness_score, joy_score, fear_score, disgust_score, anger_score),
                )
            except Exception as e:
                logging.warning("Error inserting keyword scores for keyword name", keyword["text"], "from post id", posts_id, e)
                continue

        cur.execute("UPDATE posts SET marker=1 WHERE id = ?", (posts_id,))

conn.commit()
