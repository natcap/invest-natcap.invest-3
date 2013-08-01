from invest_natcap import raster_utils
from osgeo import gdal
import numpy
import os

import logging

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('blue_carbon_preprocessor')

def get_transition_set_from_uri(dataset_uri_list):
    transitions = set([])
    dataset_list = []
    for dataset in dataset_uri_list:
        LOGGER.info("Opening: %s.", dataset)
        dataset_list.append(gdal.Open(dataset))

    n_rows = dataset_list[0].RasterYSize
    n_cols = dataset_list[0].RasterXSize

    dataset_rows = [numpy.zeros((1, n_cols)) for _ in dataset_list]
    for row_index in range(n_rows):
        for dataset_index in range(len(dataset_list)):
            dataset_list[dataset_index].ReadAsArray(
                0, row_index, n_cols, 1, buf_obj=dataset_rows[dataset_index])
        for pixel in dataset_rows:
            transitions = transitions.union(zip(pixel,pixel[1:]))

    dataset_list = None

    LOGGER.debug("Transitions: %s.", transitions)

    return transitions

def execute(args):
    transitions = get_transition_set_from_uri(args["lulc"])

    LOGGER.debug("Transitions: %s.", transitions)
