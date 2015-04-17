# cython: profile=False

import logging
import os
import collections

import numpy
cimport numpy
cimport cython
import osgeo
from osgeo import gdal
from cython.operator cimport dereference as deref

from libcpp.set cimport set as c_set
from libcpp.deque cimport deque
from libcpp.map cimport map
from libc.math cimport atan
from libc.math cimport atan2
from libc.math cimport tan
from libc.math cimport sqrt
from libc.math cimport ceil
from libc.math cimport exp

cdef extern from "time.h" nogil:
    ctypedef int time_t
    time_t time(time_t*)

import pygeoprocessing
import pygeoprocessing.routing.routing_core

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', lnevel=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('invest_natcap.seasonal_water_yield.seasonal_water_yield_core')

cdef double PI = 3.141592653589793238462643383279502884
cdef int N_BLOCK_ROWS = 16
cdef int N_BLOCK_COLS = 16

cdef calculate_recharge_c(
    precip_uri_list, et0_uri_list, flow_dir_uri, dem_uri, lulc_uri, kc_lookup,
    alpha_m, beta_i, gamma, qfi_uri,
    recharge_uri, recharge_avail_uri, vri_uri):



    LOGGER.info('calculating recharge')

def calculate_recharge(
    precip_uri_list, et0_uri_list, flow_dir_uri, dem_uri, lulc_uri, kc_lookup,
    alpha_m, beta_i, gamma, qfi_uri,
    recharge_uri, recharge_avail_uri, vri_uri):

    cdef deque[int] outlet_cell_deque

    out_dir = os.path.dirname(recharge_uri)
    outflow_weights_uri = os.path.join(out_dir, 'outflow_weights.tif')
    outflow_direction_uri = os.path.join(out_dir, 'outflow_direction.tif')

#    pygeoprocessing.routing.routing_core.find_outlets(
#        dem_uri, flow_dir_uri, outlet_cell_deque)
#    pygeoprocessing.routing.routing_core.calculate_flow_weights(
#        flow_dir_uri, outflow_weights_uri, outflow_direction_uri)

