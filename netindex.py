#!/usr/bin/env python3

import config
import csv
import logging
import os.path
import requests
from collections import namedtuple
from datetime import datetime, timedelta
from random import choice
from time import sleep

# For reference: US = 1, NC = 62, Durham = 3953, Chapel Hill = 3382

# MAYBE: Get global values
# MAYBE: Get ISP information

logger = logging.getLogger(__name__)

class NetIndex():
    """docstring for Netindex"""
    def __init__(self, base_api):
        self.base_api = base_api

        self.possible_list_units = {'country': 3, 'state': 4,
                                    'city': 5, 'isp': 6}
        self.possible_units = {'country': 3, 'state': 7, 'city': 10}
        self.possible_stats = {'dl_broadband': 0, 'ul_broadband': 1,
                               'quality': 2, 'promise': 3, 'value': 4,
                               'dl_mobile': 5, 'ul_mobile': 6}

    def generate_url(self, api_url, params):
        params_url = ["{0}={1}".format(k, v) for (k, v) in params.items()]
        full_url = "{0}?url={1}&{2}".format(self.base_api,
                                            api_url,
                                            '&'.join(params_url))
        return(full_url)

    def validate_date(self, date_text):
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect date format; should be YYYY-MM-DD.")

    def get_list(self, geo_unit, country_id=None):
        # Check for errors
        if geo_unit not in list(self.possible_list_units):
            raise ValueError("Invalid geographic level. Expected one of {0}"
                             .format(list(self.possible_list_units)))

        if geo_unit is not 'country' and country_id is None:
            raise ValueError("No unit ID. A state, city, or ISP id is required.")

        # Generate URL
        params = {'index': 0, 'index_level': self.possible_list_units[geo_unit]}

        if country_id:
            params['id'] = country_id

        url = self.generate_url('api_list.php', params)

        # Get data from API
        r = requests.get(url)
        data = r.json()

        if data.get('error_code') > 0:
            raise RuntimeError("The URL {0} resulted in an API error: {1}"
                               .format(url, data.get('error_msg')))

        return(data)

    def get_data(self, geo_unit, unit_id, stat, start_date, end_date=None):
        if not end_date:
            yesterday = datetime.today() - timedelta(1)
            end_date = yesterday.strftime('%Y-%m-%d')

        # Check for errors
        if geo_unit not in list(self.possible_units):
            raise ValueError("Invalid geographic level. Expected one of {0}"
                             .format(list(self.possible_units)))

        if stat not in list(self.possible_stats):
            raise ValueError("Invalid statistic. Expected one of {0}"
                             .format(list(self.possible_stats)))

        self.validate_date(start_date)
        self.validate_date(end_date)

        # Generate URL
        params = {'index': self.possible_stats[stat],
                  'index_start_date': start_date,
                  'index_date': end_date,
                  'index_level': self.possible_units[geo_unit],
                  'id': unit_id}

        url = self.generate_url('api_summary.php', params)

        # Get data from API
        r = requests.get(url)
        data = r.json()

        if data.get('error_code') > 0:
            raise RuntimeError("The URL {0} resulted in an API error: {1}"
                               .format(url, data.get('error_msg')))

        return(data)


def extract_states(raw_json):
    State = namedtuple('State', ['name', 'abbreviation', 'unit_id'])
    states = [State(row['label'], row['alpha_code'], row['id'])
              for row in raw_json.get('data')]
    return(states)

def extract_cities(raw_json):
    City = namedtuple('City', ['net_index_id', 'name', 'state',
                               'latitude', 'longitude'])
    cities = [City(row['id'], row['label'][:-4], row['label'][-2:],
                   row['latitude'], row['longitude'])
              for row in raw_json.get('data')]
    return(cities)

def parse_city(raw_json):
    # TODO: Make sure these are all the values wanted (i.e. no IP addresses or # ISPs)
    Statistic = namedtuple('Statistic', ['date', 'value'])
    data = [Statistic(row['aggregate_date'], row['index_value'])
            for row in raw_json.get('data').get('index_values')]
    return(data)


if __name__ == '__main__':
    net = NetIndex(base_api='http://explorer.netindex.com/apiproxy.php')

    cities = extract_cities(net.get_list(geo_unit='city', country_id=1))[0:2]

    # Save cities to CSV
    logger.info("Saving full list of cities to {0}.".format(config.CITIES_FILE))
    with open(config.CITIES_FILE, 'w', newline='') as csvfile:
        w = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        w.writerow(cities[0]._fields)

        for city in cities:
            w.writerow(city)

    # Save city data to CSV
    Stat = namedtuple('Stat', ['net_index_id', 'date', 'stat', 'value'])

    logger.info("Downloading data for each city.")
    for i, city in enumerate(cities):
        rows = []

        logger.info("Getting data for {0}, {1} (ID: {2})."
                    .format(city.name, city.state, city.net_index_id))

        # Get all the statistics for each city and save to list of dictionaries
        for stat in list(net.possible_stats):
            city_data = net.get_data(geo_unit='city', unit_id=city.net_index_id,
                                     stat=stat, start_date='2000-01-01')

            parsed = parse_city(city_data)

            for entry in parsed:
                row = Stat(city.net_index_id, entry.date, stat, entry.value)
                rows.append(row)

        # Write to CSV
        logger.info("Saving to {0}.".format(config.CITY_DATA_FILE))
        file_exists = os.path.isfile(config.CITY_DATA_FILE)

        with open(config.CITY_DATA_FILE, 'a') as csvfile:
            w = csv.writer(csvfile, delimiter=',', lineterminator='\n')

            if not file_exists:  # Header
                w.writerow(rows[0]._fields)

            for row in rows:
                w.writerow(row)

        # Pause to be nice to the API
        if i != len(cities) - 1:
            wait = choice(config.WAIT_RANGE)
            logger.info("{0} cities left to do.".format(len(cities) - 1))
            logger.info("Waiting for {0} seconds before moving on.".format(wait))
            sleep(wait)
        else:
            logger.info("All done! \(•◡•)/")
