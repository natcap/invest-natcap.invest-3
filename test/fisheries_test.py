'''This will be the test module for the non-core portion of Fisheries.'''

import os
import logging
import glob
import filecmp

import invest_natcap.testing

from invest_natcap.habitat_risk_assessment import hra

LOGGER = logging.getLogger('fisheries_test')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class TestHRA(invest_natcap.testing.GISTest):

