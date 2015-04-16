"""InVEST Seasonal Water Yield Model"""

import logging

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger(
    'invest_natcap.seasonal_water_yield.seasonal_water_yield')

def execute(args):
    """This function invokes the seasonal water yield model given
        URI inputs of files. It may write log, warning, or error messages to
        stdout.
    """

    LOGGER.debug(args)
