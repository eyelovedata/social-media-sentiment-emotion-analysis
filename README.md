# Sentiment and Emotion Analysis
Using IBM Watson Natural Language Understanding to perform sentiment and emotion analysis 

Currently contains an example script illustrating how to use IBM Watson's Natural Language Understanding to perform sentiment and emotion analysis. This example script assumes that the items to be analyzed are "posts," e.g. free text posts made by users on some platform. 
Data are assumed to be stored in a sqlite database. 

Script uses the API to feed the posts to the IBM Watson NLU service, obtains sentiment and emotion scores, and stores the resulting scores back into the database in new tables. 

You will need your own API Key for access to the service 

Requires: 
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
