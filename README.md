[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3989936.svg)](https://doi.org/10.5281/zenodo.3989936)

# Data Mining for Sentiment and Emotion Analysis
A method for sentiment and emotion analysis in medicine using IBM Watson's Natural Language Understanding and MedHelp data source to help guide clinicians to better understand patients' perspectives. Scripts can be adapted to other social media platforms.

## Summary
Scripts allow full extraction of patient-doctor conversations on MedHelp into an SQLite relational database. Data is fed into IBM Watson Natural Language Understanding API, which returns sentiment scores (positive, neutral, negative) and emotions likelihood (anger, disgust, fear, joy, sadness) for every text entity given, along with associated sentiment scores and emotions likelihood for important keywords detected by Watsons' algorithms. Keywords are linguistically processed to group keywords with the same clinical relevance. Basic data aggregation is performed on the dataset. Instructions are given within each script to guide users when needed.

**NOTE**: the MedHelp data mining tool is designed to scrape the platform as of January 1<sup>st</sup>, 2020. Changes to the platform can result in necessary modifications to the code.

A chart for the oculoplastics field using this project can be found [here](https://oculoplastics-keywords.herokuapp.com/) (oculoplastics-keywords-chart.html).

## Installation
**NOTE**: Python 3.6 or higher is required.
```bash
# clone the repo
$ git clone git@github.com:eyelovedata/social-media-sentiment-emotion-analysis.git

# change the working directory to social-media-sentiment-emotion-analysis
$ cd social-media-sentiment-emotion-analysis

# install python3 and python3-pip if they are not installed

# install the requirements
$ python3 -m pip install -r requirements.txt
```

## Scripts
### 1. Thread extraction 
**medhelp-thread-extraction.py**

**NOTE**: requires an SQLite database to be setup prior to running the script

Prompts the user to enter a search term, extracts relevant thread information (url, title, forum, html) for the given search term and inserts the results into the database. Errors are logged when the script completes.

### 2. Post and user extraction
**medhelp-post-user-extraction.py**

For each previously extracted thread, the content of each user (username, doctor, profile url, profile html, age, sex, member since, location) and post (users_id, threads_id, order, content, date) are extracted and inserted into the database. Errors are logged when the script completes.

### 3. IBM Watson NLU sentiment/emotion analysis
**ibm-watson-nlu-posts-keywords-sentiment-emotion-extraction.py**

**NOTE**: requires an API-key to access the service

Assumes that the SQLite database contains a posts table with the following headers: content, label, sent_score, anger_score, sadness_score, fear_score, disgust_score, and joy_score. Feeds the content of each post to IBM Watson NLU sentiment and emotion analysis, which returns sentiment scores and emotions likelihood for each whole post and important keywords within each post, and inserts the results into the database.

### 4. Keyword processing and aggregation
**keyword-processing-aggregating.ipynb**

Processes the keywords (lowercasing, punctuation removal, stop word deletion, lemmatization) into cleaned keywords, does basic aggregation of the processed keywords (frequency, mean, scores, standard deviation) and outputs the results to a csv. Helps the user visualize their data.
