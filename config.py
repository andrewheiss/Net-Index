import sys
import logging
import logging.config


CITIES_FILE = "cities.csv"
CITY_DATA_FILE = "city_data.csv"
LOG_FILE = "netindex.log"
WAIT_RANGE = range(5, 10)


# ------------
# Set up log
# ------------
# http://victorlin.me/posts/2012/08/26/good-logging-practice-in-python
LOG_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(levelname)-8s %(asctime)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            "class": "logging.FileHandler",
            'filename': LOG_FILE,
            'mode': 'a',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO',  # Max level overall
            'propagate': True
        }
    }
}

# Function to redirect exceptions to the log
# Via http://stackoverflow.com/a/16993115/120898
# Assign to sys.excepthook like so:
#   sys.excepthook = handle_exception
def handle_exception(exc_type, exc_value, exc_traceback):
    # Ignore KeyboardInterrupt so a console Python program can exit with Ctrl + C
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Uncaught exception",
                  exc_info=(exc_type, exc_value, exc_traceback))

# Load log configuration
logging.config.dictConfig(LOG_SETTINGS)

# Requests is too verbose. Turn the level down to WARNING.
logging.getLogger("requests").setLevel(logging.WARNING)

# Send exceptions to the log too
sys.excepthook = handle_exception

# Start the log
logger = logging.getLogger(__name__)
logger.info("Configuration file loaded. Ready to start.")
