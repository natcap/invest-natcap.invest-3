"""InVEST Seasonal Water Yield Model"""

import os
import logging

import numpy
import gdal
import pygeoprocessing

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

def calculate_quick_flow(
        precip_uri_list, rain_events_table_uri, lulc_uri, soil_group_uri,
        cn_table_uri):
    """Calculates quick flow """

    output_dir = r"C:\Users\rich\Documents\delete_seasonal_water_yield_output"

    LOGGER.info('calculating curve number')
    cn_lookup = pygeoprocessing.geoprocessing.get_lookup_from_table(
        cn_table_uri, 'lucode')
    cn_lookup = dict([
        (lucode, cn_lookup[lucode]['cn']) for lucode in cn_lookup])

    cn_uri = os.path.join(output_dir, 'cn.tif')
    cn_nodata = -1
    pygeoprocessing.geoprocessing.reclassify_dataset_uri(
        lulc_uri, cn_lookup, cn_uri, gdal.GDT_Float32, cn_nodata,
        exception_flag='values_required')

    si_nodata = -1
    def si_op(ci):
        """potential maximum retention"""
        si = 1000.0 / ci - 10
        return numpy.where(ci != cn_nodata, si, si_nodata)

    LOGGER.info('calculating Si')
    si_uri = os.path.join(output_dir, 'si.tif')
    pixel_size = pygeoprocessing.geoprocessing.get_cell_size_from_uri(lulc_uri)
    pygeoprocessing.geoprocessing.vectorize_datasets(
        [cn_uri], si_op, si_uri, gdal.GDT_Float32,
        si_nodata, pixel_size, 'intersection', vectorize_op=False,
        datasets_are_pre_aligned=True)


"""
    #calculate Si from curve number
    Si = 1000 / CNi - 10
    #calculate quickflow as

    for m in range(12):
        QFi[m] = (
            25.4 * n[m] * (
                (P[m]/n[m]/25.4 -0.2 * S)**2 / (P[m]/n[m]/25.4 +0.8 * S)))

    total_QFi = sum(QFi)
"""

def main():
    """main entry point"""

    cn_table_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\cn.csv"
    precip_uri_list = None
    rain_events_table_uri = None
    lulc_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\nass_sw_lulc.tif"
    soil_group_uri = None

    calculate_quick_flow(precip_uri_list, rain_events_table_uri, lulc_uri,
        soil_group_uri, cn_table_uri)

if __name__ == '__main__':
    main()
