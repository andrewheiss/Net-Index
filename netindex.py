#!/usr/bin/env python3

import requests
import json

# TODO: Get global values
# MAYBE: Get ISP information
# MAYBE: Filter states in full list?

class NetIndex():
    """docstring for Netindex"""
    def __init__(self, base_api):
        self.base_api = base_api

    def generate_url(self, api_url, params):
        params_url = ["{0}={1}".format(k, v) for (k, v) in params.items()]
        full_url = "{0}?url={1}&{2}".format(self.base_api,
                                            api_url,
                                            '&'.join(params_url))
        return(full_url)

    def get_list(self, geo_unit, country_id=None):
        possible_units = {'country': 3, 'state': 4, 'city': 5, 'isp': 6}

        if geo_unit not in list(possible_units):
            raise ValueError("Invalid geographic level. Expected one of {0}"
                             .format(list(possible_units)))

        if geo_unit is not 'country' and country_id is None:
            raise ValueError("No unit ID. A state, city, or ISP id is required.")

        params = {'index': 0, 'index_level': possible_units[geo_unit]}

        if country_id:
            params['id'] = country_id

        url = self.generate_url('api_list.php', params)
        r = requests.get(url)
        data = r.json()

        if data.get('error_code') > 0:
            raise RuntimeError("The URL {0} resulted in an API error: {1}"
                               .format(url, data.get('error_msg')))

        return(data)

    def get_data(self, geo_unit, unit_id, stat, start_date, end_date=None):
        possible_units = {'country': 3, 'state': 7, 'city': 10}
        possible_stats = {'dl_broadband': 0, 'ul_broadband': 1,
                          'quality': 2, 'promise': 3, 'value': 4,
                          'dl_mobile': 5, 'ul_mobile': 6}

        if geo_unit not in list(possible_units):
            raise ValueError("Invalid geographic level. Expected one of {0}"
                             .format(list(possible_units)))

        if stat not in list(possible_stats):
            raise ValueError("Invalid statistic. Expected one of {0}"
                             .format(list(possible_stats)))

        params = {'index': possible_stats[stat],
                  'index_start_date': start_date,
                  'index_date': end_date,
                  'index_level': possible_units[geo_unit],
                  'id': unit_id}

        url = self.generate_url('api_summary.php', params)
        r = requests.get(url)
        data = r.json()

        if data.get('error_code') > 0:
            raise RuntimeError("The URL {0} resulted in an API error: {1}"
                               .format(url, data.get('error_msg')))

        return(data)


if __name__ == '__main__':
    # Logic:
    # 1. Get list of states or cities (allow specific state? Create function that lists all cities in a given state?)
    # 2. Loop through each id and get 7 statistics from each
    # 3. Save as CSV

    net = NetIndex(base_api='http://explorer.netindex.com/apiproxy.php')

    # data = net.get_list(geo_unit='state', country_id=1)

    # data = net.get_data(geo_unit='country', unit_id=1, stat='dl_broadband',
    # data = net.get_data(geo_unit='state', unit_id=62, stat='dl_broadband',
    data = net.get_data(geo_unit='city', unit_id=3953, stat='dl_broadband',
                        start_date='2015-07-21', end_date='2015-07-23')
    print(data)
