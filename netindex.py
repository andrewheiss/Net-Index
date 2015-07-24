#!/usr/bin/env python3

import json
import requests
from collections import namedtuple
from datetime import datetime, timedelta

# TODO: Get global values
# MAYBE: Get ISP information
# MAYBE: Filter states in full list?

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
    City = namedtuple('City', ['name', 'state', 'unit_id'])
    cities = [City(row['label'][:-4], row['label'][-2:], row['id'])
              for row in raw_json.get('data')]
    return(cities)


if __name__ == '__main__':
    # Logic:
    # 1. Get list of states or cities (allow specific state? Create function that lists all cities in a given state?)
    # 2. Loop through each id and get 7 statistics from each
    # 3. Save as CSV

    net = NetIndex(base_api='http://explorer.netindex.com/apiproxy.php')

    # states = extract_states(net.get_list(geo_unit='state', country_id=1))
    cities = extract_cities(net.get_list(geo_unit='city', country_id=1))
    for city in cities:
        print(city.name)

    # data = net.get_data(geo_unit='country', unit_id=1, stat='dl_broadband',
    # data = net.get_data(geo_unit='state', unit_id=62, stat='dl_broadband',
    # data = net.get_data(geo_unit='city', unit_id=3953, stat='dl_broadband',
    #                     start_date='2015-07-21')
    # print(data)
