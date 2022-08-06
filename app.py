"""app for covid-dashboard"""
from datetime import datetime
from flask import Flask, request, render_template
from covid_data_handler import covid_data, schedule_covid_updates, update_covid_data, remove_covid_update, covid_shed
from covid_news_handling import news, schedule_news_updates, update_news, remove_news_update, news_shed,deleted_news, NEWS_ARTICLES_LIMIT

app = Flask(__name__)
updates = []

update_covid_data()
update_news()



@app.route('/')
@app.route('/index')
def index():
    
    notif = request.args.get('notif')
    update_item = request.args.get('update_item')
    update = request.args.get('update')
    if notif:
        deleted_news.add(notif)
        for i, item in enumerate(news['articles']):
            if item['title'] == notif:
                del news['articles'][i]
                break
    if update_item:
        for i, item in enumerate(updates):
            if item['title'] == update_item:
                del updates[i]
                break
        remove_covid_update(update_item)
        remove_news_update(update_item)

    if update:
        label = request.args.get('two')
        repeat = request.args.get('repeat')
        covid_data_update = request.args.get('covid-data')
        news_update = request.args.get('news')

        updates.append({
            'title': label,
            'content': f"Update at {update}, repeat= {bool(repeat)}, covid data= {bool(covid_data_update)}, news= {bool(news_update)}",
            'repeat': bool(repeat),
            'covid_data': bool(covid_data_update),
            'news' : bool(news_update)
        })
        update_name = label
        if repeat:
            update_name += '_repeat'
        hour, minute = update.split(':')
        now = datetime.now()
        update_time = datetime.now().replace(hour=int(hour), minute=int(minute))
        update_interval = (update_time - now).seconds
        if update_interval < 0:
            update_interval += 24 * 60 * 60
        if covid_data_update:
            schedule_covid_updates(update_interval, update_name)
        if news_update:
            schedule_news_updates(update_interval, update_name)
    covid_shed.run(blocking=False)
    news_shed.run(blocking=False)
    return render_template('ECM1400 Flask Form Bootstrap Template.html', 
        image = "https://www.ird.fr/sites/ird_fr/files/2020-03/Center%20for%20diseases%20and%20prevention.jpg",
        title='Covid data',
        updates=updates,
        location=covid_data['location'],
        local_7day_infections=covid_data['local_7day_infections'],
        nation_location=covid_data['nation_location'],
        national_7day_infections=covid_data['national_7day_infections'],
        hospital_cases=covid_data['hospital_cases'],
        deaths_total=covid_data['deaths_total'],
        news_articles=news['articles'][:NEWS_ARTICLES_LIMIT],
    )