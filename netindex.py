#!/usr/bin/env python3

# --------------
# Load modules
# --------------
# My modules
import config

# Full modules
import csv
import logging
import os
import os.path
import requests
import zipfile

# Just parts of modules
from collections import namedtuple
from datetime import datetime, timedelta
from random import choice, gauss
from time import sleep

# Start log
logger = logging.getLogger(__name__)


# ------------
# API method
# ------------
class NetIndex():
    """Generate API URLs for Ookla's Net Index.

    The undocumented Net Index API uses different combination of HTTP GET
    variables to query the underlying database and return JSON data. This
    function makes those parameters more human readable and easier to use.

    The class has two primary functions: get_list() for retrieving a list of
    countries, states, or cities in the Net Index database, and get_data() for
    retrieving internet statistics for a given geographic unit.

    Args:
        base_api (str): The base URL for the Net Index API

    Returns:
        A NetIndex object that can make API calls using get_list() and get_data()

    """
    def __init__(self, base_api='http://explorer.netindex.com/apiproxy.php'):
        self.base_api = base_api

        self.possible_list_units = {'country': 3, 'state': 4,
                                    'city': 5, 'isp': 6}
        self.possible_units = {'country': 3, 'state': 7, 'city': 10}
        self.possible_stats = {'dl_broadband': 0, 'ul_broadband': 1,
                               'quality': 2, 'promise': 3, 'value': 4,
                               'dl_mobile': 5, 'ul_mobile': 6}

    def _generate_url(self, api_url, params):
        """Generate a URL to make an API call.

        Args:
            api_url (str): Base URL for the API
                           (e.g. http://explorer.netindex.com/apiproxy.php)
            params (dict): A dictionary of parameters to format as GET variables
                           in the URL (e.g. {'index_start_date': '2000-01-01',
                                             'index': 6, 'id': '3', 'index_level': 10,
                                             'index_date': '2015-07-27'})

        Returns:
            A complete URL
            (e.g. http://explorer.netindex.com/apiproxy.php?url=api_summary.php&
                         index_start_date=2000-01-01&id=3&index=5&
                         index_level=10&index_date=2015-07-27)
        """
        params_url = ["{0}={1}".format(k, v) for (k, v) in params.items()]
        full_url = "{0}?url={1}&{2}".format(self.base_api,
                                            api_url,
                                            '&'.join(params_url))
        return(full_url)

    def _validate_date(self, date_text):
        """Ensure that a given string follows the ISO 8601 format.

        Args:
            date_text (str): Date string to be checked

        Raises:
            ValueError: If date_text is not an ISO 8601 date
        """
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect date format; should be YYYY-MM-DD.")

    def get_list(self, geo_unit, country_id=None):
        """Get a list of JSON-encoded data for a given level of geographic
        unit (country, state, city, ISP).

        Args:
            geo_unit (str): One of 'country', 'state', 'city', or 'isp'
            country_id (int): The id of the country that contains the desired
                              states, cities, or ISPs
                              (e.g. United States = 1)

        Returns:
            JSON-encoded Net Index data
        """
        # Check for errors
        if geo_unit not in list(self.possible_list_units):
            raise ValueError("Invalid geographic level. Expected one of {0}"
                             .format(list(self.possible_list_units)))

        if geo_unit is not 'country' and country_id is None:
            raise ValueError("No unit ID. A state, city, or ISP id is required.")

        # Generate URL
        params = {'index': 0, 'index_level': self.possible_list_units[geo_unit]}

        # Add country_id to URL parameters if given
        if country_id:
            params['id'] = country_id

        url = self._generate_url('api_list.php', params)

        # Get data from API
        s = requests.session()
        s.headers.update({"User-Agent": choice(config.user_agents)})
        r = s.get(url)
        data = r.json()

        if data.get('error_code') > 0:
            raise RuntimeError("The URL {0} resulted in an API error: {1}"
                               .format(url, data.get('error_msg')))

        return(data)

    def get_data(self, geo_unit, unit_id, stat, start_date, end_date=None):
        """Get JSON-encoded data for a given internet statistic for given
        geographic unit over a given time period.

        Args:
            geo_unit (str): One of 'country', 'state', or 'city'
            unit_id (id): ID for geographic unit (retrieved from get_list()).
                          E.g. North Carolina = 62; Durham = 3953; Chapel Hill = 3382
            stat (str): Statistic to be collected. One of 'dl_broadband',
                        'ul_broadband', 'quality', 'promise', 'value',
                        'dl_mobile', or 'ul_mobile'
            start_date (str): Date formatted as YYYY-MM-DD (ISO 8601)
            end_date (Optional[str]): Date formatted as YYYY-MM-DD (ISO 8601).
                                      Defaults to the previous day.

        Returns:
            JSON-encoded Net Index data
        """
        # Use yesterday's date if no end date provided
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

        self._validate_date(start_date)
        self._validate_date(end_date)

        # Generate URL
        params = {'index': self.possible_stats[stat],
                  'index_start_date': start_date,
                  'index_date': end_date,
                  'index_level': self.possible_units[geo_unit],
                  'id': unit_id}

        url = self._generate_url('api_summary.php', params)

        # Get data from API
        s = requests.session()
        s.headers.update({"User-Agent": choice(config.user_agents)})
        r = s.get(url)
        data = r.json()

        if data.get('error_code') > 0:
            raise RuntimeError("The URL {0} resulted in an API error: {1}"
                               .format(url, data.get('error_msg')))

        return(data)


# ------------------------------
# Helper functions for parsing
# ------------------------------
def extract_states(raw_json):
    """Map raw JSON to a named tuple of state-specific metadata."""
    State = namedtuple('State', ['name', 'abbreviation', 'unit_id'])
    states = [State(row['label'], row['alpha_code'], row['id'])
              for row in raw_json.get('data')]
    return(states)

def extract_cities(raw_json):
    """Map raw JSON to a named tuple of city-specific metadata."""
    City = namedtuple('City', ['net_index_id', 'name', 'state',
                               'latitude', 'longitude'])
    cities = [City(row['id'], row['label'][:-4], row['label'][-2:],
                   row['latitude'], row['longitude'])
              for row in raw_json.get('data')]
    return(cities)

def parse_city(raw_json):
    """Map raw JSON to a named tuple of city-specific internet statistics."""
    Statistic = namedtuple('Statistic', ['date', 'value'])
    data = [Statistic(row['aggregate_date'], row['index_value'])
            for row in raw_json.get('data').get('index_values')]
    return(data)


# ---------------
# Actual script
# ---------------
if __name__ == '__main__':
    net = NetIndex()

    # -------------------------------
    # Deal with city-level metadata
    # -------------------------------
    # Get list of all cities in database
    cities = extract_cities(net.get_list(geo_unit='city', country_id=1))[0:2]

    # Save cities to CSV
    logger.info("Saving full list of cities to {0}.".format(config.CITIES_FILE))
    with open(config.CITIES_FILE, 'w', newline='') as csvfile:
        w = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        w.writerow(cities[0]._fields)

        for city in cities:
            w.writerow(city)

    # --------------------------------
    # Deal with individual city data
    # --------------------------------
    # Save individual city data to CSV
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
            wait = abs(gauss(config.WAIT_AVG, config.WAIT_STDEV))
            logger.info("Waiting for {0} seconds before moving on.".format(round(wait, 2)))
            sleep(wait)
        else:
            logger.info("All done scraping!")

    # --------------------
    # Finalize CSV files
    # --------------------
    # Rename city metadata
    parts = os.path.splitext(config.CITIES_FILE)
    new_name = parts[0] + '_final' + parts[1]
    logger.info("Renaming {0} to {1}".format(config.CITIES_FILE, new_name))
    os.rename(config.CITIES_FILE, new_name)

    # Rename actual daily city data
    parts = os.path.splitext(config.CITY_DATA_FILE)
    new_name = parts[0] + '_raw_final' + parts[1]
    logger.info("Renaming {0} to {1}".format(config.CITIES_FILE, new_name))
    os.rename(config.CITY_DATA_FILE, new_name)

    # Zip up city data (because it's crazy huge)
    zip_parts = os.path.splitext(new_name)
    zip_new_name = zip_parts[0] + '.zip'
    logger.info("Compressing city data to {0}".format(zip_new_name))
    with zipfile.ZipFile(zip_new_name, 'w',
                         compression=zipfile.ZIP_DEFLATED) as myzip:
        myzip.write(new_name, arcname=os.path.basename(zip_parts[0]) + '.csv')

    assert(os.path.isfile(zip_new_name))
    assert(os.stat(zip_new_name).st_size > 0)
    os.remove(new_name)

    logger.info("All done with everything! \(•◡•)/")
