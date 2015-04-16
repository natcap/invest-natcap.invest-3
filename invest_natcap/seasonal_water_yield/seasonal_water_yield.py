"""InVEST Seasonal Water Yield Model"""

import os
import logging
import re
import sys

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
        cn_table_uri, aoi_uri, cn_uri, qfi_uri, intermediate_dir):
    """Calculates quick flow """

    output_wkt = gdal.Open(lulc_uri).GetProjection()
    LOGGER.info(output_wkt)

    LOGGER.info('loading number of monthly events')
    rain_events_lookup = pygeoprocessing.geoprocessing.get_lookup_from_table(
        rain_events_table_uri, 'month')
    n = dict([
        (month, rain_events_lookup[month]['events'])
        for month in rain_events_lookup])

    LOGGER.info('calculating curve number')
    cn_lookup = pygeoprocessing.geoprocessing.get_lookup_from_table(
        cn_table_uri, 'lucode')
    cn_lookup = dict([
        (lucode, cn_lookup[lucode]['cn']) for lucode in cn_lookup])

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
    si_uri = os.path.join(intermediate_dir, 'si.tif')
    pixel_size = pygeoprocessing.geoprocessing.get_cell_size_from_uri(lulc_uri)
    pygeoprocessing.geoprocessing.vectorize_datasets(
        [cn_uri], si_op, si_uri, gdal.GDT_Float32,
        si_nodata, pixel_size, 'intersection', vectorize_op=False,
        aoi_uri=aoi_uri, datasets_are_pre_aligned=True)

    qf_nodata = -1.0
    qf_monthly_uri_list = []
    for m in range(1, 13):
        projected_precip_uri = os.path.join(
            intermediate_dir, 'precip_%d.tif' % m)
        LOGGER.info('projecting precip %d' % m)
        pygeoprocessing.geoprocessing.reproject_dataset_uri(
            precip_uri_list[m-1], pixel_size, output_wkt, 'nearest',
            projected_precip_uri)

        qf_monthly_uri_list.append(
            os.path.join(intermediate_dir, 'qf_%d.tif' % m))

        P_nodata = pygeoprocessing.geoprocessing.get_nodata_from_uri(
            precip_uri_list[m-1])
        def qf_op(Pm, S):
            """calculate quickflow"""
            numerator = 25.4 * n[m] * (Pm/float(n[m])/25.4 - 0.2 * S)**2
            denominator = Pm/float(n[m])/25.4 +0.8 * S
            return numpy.where(
                (Pm == P_nodata) | (S == si_nodata) | (denominator == 0),
                qf_nodata, numerator / denominator)

        LOGGER.info('calculating QFim')
        pygeoprocessing.geoprocessing.vectorize_datasets(
            [projected_precip_uri, si_uri], qf_op, qf_monthly_uri_list[m-1],
            gdal.GDT_Float32, qf_nodata, pixel_size, 'intersection',
            vectorize_op=False, aoi_uri=aoi_uri)

    LOGGER.info('calculating QFi')

    def qfi_sum(*qf_values):
        """sum the monthly qfis"""
        return numpy.where(
            qf_values[0] == qf_nodata, numpy.add(qf_values), qf_nodata)
    pygeoprocessing.geoprocessing.vectorize_datasets(
        qf_monthly_uri_list, qfi_sum, qfi_uri,
        gdal.GDT_Float32, qf_nodata, pixel_size, 'intersection',
        vectorize_op=False)


def main():
    """main entry point"""

    pet_dir = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\pet"
    precip_dir = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\precip"


    aoi_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\MonthlyWaterYield\input\Subwatershed1\subws_id1.shp"
    cn_table_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\cn.csv"
    rain_events_table_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\Number of events.csv"
    precip_uri_list = []
    pet_uri_list = []

    pet_dir_list = [os.path.join(pet_dir, f) for f in os.listdir(pet_dir)]
    precip_dir_list = [
        os.path.join(precip_dir, f) for f in os.listdir(precip_dir)]

    for month_index in range(1, 13):
        month_file_match = re.compile('.*[^\d]%d\.[^.]+$' % month_index)

        for data_type, dir_list, uri_list in [
                ('PET', pet_dir_list, pet_uri_list),
                ('Precip', precip_dir_list, precip_uri_list)]:

            file_list = [x for x in dir_list if month_file_match.match(x)]
            if len(file_list) == 0:
                raise ValueError(
                    "No %s found for month %d" % (data_type, month_index))
            if len(file_list) > 1:
                raise ValueError(
                    "Ambiguous set of files found for month %d: %s" %
                    (month_index, file_list))
            uri_list.append(file_list[0])

    print pet_uri_list
    print precip_uri_list

    output_dir = r"C:\Users\rich\Documents\delete_seasonal_water_yield_output"

    pygeoprocessing.geoprocessing.create_directories([output_dir])

    qfi_uri = os.path.join(output_dir, 'qf.tif')
    cn_uri = os.path.join(output_dir, 'cn.tif')
    lulc_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\nass_sw_lulc.tif"
    soil_group_uri = None

    calculate_quick_flow(
        precip_uri_list, rain_events_table_uri, lulc_uri, soil_group_uri,
        cn_table_uri, aoi_uri, cn_uri, qfi_uri, output_dir)

if __name__ == '__main__':
    main()
