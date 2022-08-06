import requests
import json
import sched, time
import logging
import sys

with open("config.json") as config_file:
    config = json.load(config_file)
    NEWS_API_KEY = config['NEWS_API_KEY']
    NEWS_ARTICLES_LIMIT = config['NEWS_ARTICLES_LIMIT']
    LOG_FILE = config['LOG_FILE']

# https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file


file_handler = logging.FileHandler(filename='logs.log')
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)


news_shed = sched.scheduler(time.time, time.sleep)

news = {}
deleted_news = set()
news_updates = {}




def news_API_request(covid_terms="Covid COVID-19 coronavirus"):
    """calls the API"""
    responce = requests.get(f"https://newsapi.org/v2/everything?q={covid_terms}&apiKey={NEWS_API_KEY}")
    return responce.json()

def schedule_news_updates(update_interval, update_name):
    """scheduler for news updates, update interval of 1"""
    logging.info('schedule_news_updates ...')
    news_updates[update_name] = news_shed.enter(update_interval, 1, update_news, argument=(update_name,))

def remove_news_update(update_name):
    """removes news updates"""
    if update_name in news_updates:
        try:
            news_shed.cancel(news_updates[update_name])
        except ValueError:
            pass
        del news_updates[update_name]

def update_news(update_name=None):
    """checks for news updates, also checks if updates have already been removed so they are not shown again
    if news update is repeated, adds 1 day to the date"""
    logging.info('updating news ... ')
    articles = news_API_request()['articles']
    
    for i, item in enumerate(articles):
            if item['title'] in deleted_news:
                del articles[i]
    news['articles'] = articles
    if update_name and 'repeat' in update_name:
        logging.info('repeating ...')

        schedule_news_updates(24 * 60 * 60, update_name)