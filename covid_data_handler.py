

import sched, time
import csv, json
import logging
import sys

from uk_covid19 import Cov19API

with open("config.json") as config_file:
    config = json.load(config_file)
    LOCATION = config['LOCATION']
    NATION_LOCATION = config['NATION_LOCATION']
    LOG_FILE = config['LOG_FILE']


# https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log-file

"""sets up logging"""
file_handler = logging.FileHandler(filename=LOG_FILE)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)

col_names = ["areaCode", "areaName", "areaType", "date", "cumDailyNsoDeathsByDeathDate", "hospitalCases", "newCasesBySpecimenDate"]
covid_data = {}
covid_updates = {}




covid_shed = sched.scheduler(time.time, time.sleep)


def parse_csv_data(csv_filename):
    """ converts provided csv file to a list """
    covid_data = []
    with open(csv_filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        covid_data = []
        for row in csv_reader:
            covid_data.append(row)
        return covid_data


def process_covid_csv_data(covid_csv_data):
    """ converts covid data as a list into 3 variables: number of cases
    in the last 7 days, the current number of hospital cases, and the 
    cumulative number of deaths """
    cases_week = 0
    hospital_cases = 0
    deaths = 0
    for i in covid_csv_data[3:10]:
        cases_week += int(i[6])
    hospital_cases = covid_csv_data[1][5]
    hospital_cases = int(hospital_cases)
    for k in covid_csv_data[1:]:
        if k[4]:
            deaths = int(k[4])
            break
    return cases_week, hospital_cases, deaths

def process_covid_api_data(covid_api_data):
    """processes data called by the  API """
    covid_api_data = covid_api_data["data"]
    cases_week = 0
    hospital_cases = 0
    deaths = 0
    for i in covid_api_data[2:9]:
        cases_week += i['newCasesBySpecimenDate']
    if 'hospitalCases' in covid_api_data[0]:
        hospital_cases = covid_api_data[0]['hospitalCases']
        for k in covid_api_data:
            deaths = k['cumDailyNsoDeathsByDeathDate']

            if deaths:
                break
    return cases_week, hospital_cases, deaths


def covid_API_request(location = "Exeter", location_type = "ltla"):
    """ takes location and location type and searches for covid data relating to the location """
    area = [
        'areaType=' + location_type,
        'areaName=' + location
    ]

    api = Cov19API(filters=area, structure=col_names)

    data = api.get_json()
    return data


def schedule_covid_updates(update_interval, update_name):
    """schedules updates for the data and news articles"""
    logging.info('schedule_covid_updates ...')
    covid_updates[update_name] = covid_shed.enter(update_interval, 1, update_covid_data, argument=(update_name,))

def remove_covid_update(update_name):
    if update_name in covid_updates:
        try:
            covid_shed.cancel(covid_updates[update_name])
        except ValueError:
            pass
        del covid_updates[update_name]



def update_covid_data(update_name=None, location=LOCATION, nation_location=NATION_LOCATION):
    """calls codid data from the dictionary"""
    logging.info("updating covid data ...")
    national_7day_infections, hospital_cases, deaths_total = process_covid_api_data(covid_API_request(location, "nation"))
    local_7day_infections, _, _ = process_covid_api_data(covid_API_request(nation_location))
    covid_data["location"] = location
    covid_data["local_7day_infections"] = local_7day_infections
    covid_data["nation_location"] = nation_location
    covid_data["national_7day_infections"] = national_7day_infections
    covid_data["hospital_cases"] = hospital_cases
    covid_data["deaths_total"] = deaths_total
    if update_name and 'repeat' in update_name:
        logging.info('repeating ...')
        schedule_covid_updates(24 * 60 * 60, update_name)