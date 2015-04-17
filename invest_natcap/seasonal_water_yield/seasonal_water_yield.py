"""InVEST Seasonal Water Yield Model"""

import os
import logging
import re

import numpy
import gdal
import pygeoprocessing
import pygeoprocessing.routing


logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger(
    'invest_natcap.seasonal_water_yield.seasonal_water_yield')

N_MONTHS = 12

def execute(args):
    """This function invokes the seasonal water yield model given
        URI inputs of files. It may write log, warning, or error messages to
        stdout.
    """

    LOGGER.debug(args)

def calculate_quick_flow(
        precip_uri_list, rain_events_table_uri, lulc_uri,
        cn_table_uri, cn_uri, qfi_uri, intermediate_dir):
    """Calculates quick flow """



    LOGGER.info('loading number of monthly events')
    rain_events_lookup = pygeoprocessing.geoprocessing.get_lookup_from_table(
        rain_events_table_uri, 'month')
    n_events = dict([
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
    def si_op(ci_array):
        """potential maximum retention"""
        si_array = 1000.0 / ci_array - 10
        return numpy.where(ci_array != cn_nodata, si_array, si_nodata)

    LOGGER.info('calculating Si')
    si_uri = os.path.join(intermediate_dir, 'si.tif')
    pixel_size = pygeoprocessing.geoprocessing.get_cell_size_from_uri(lulc_uri)
    pygeoprocessing.geoprocessing.vectorize_datasets(
        [cn_uri], si_op, si_uri, gdal.GDT_Float32,
        si_nodata, pixel_size, 'intersection', vectorize_op=False,
        datasets_are_pre_aligned=True)

    qf_nodata = -1.0
    qf_monthly_uri_list = []
    p_nodata = pygeoprocessing.geoprocessing.get_nodata_from_uri(
        precip_uri_list[0])

    for m_index in range(1, N_MONTHS + 1):
        qf_monthly_uri_list.append(
            os.path.join(intermediate_dir, 'qf_%d.tif' % m_index))

        def qf_op(pm_array, s_array):
            """calculate quickflow"""
            numerator = (
                25.4 * n_events[m_index] *
                (pm_array/float(n_events[m_index])/25.4 - 0.2 * s_array)**2)
            denominator = pm_array/float(n_events[m_index])/25.4 +0.8 * s_array
            return numpy.where(
                (pm_array == p_nodata) | (s_array == si_nodata) |
                (denominator == 0), qf_nodata, numerator / denominator)

        LOGGER.info('calculating QFi_%d of %d', m_index, N_MONTHS)
        pygeoprocessing.geoprocessing.vectorize_datasets(
            [precip_uri_list[m_index-1], si_uri], qf_op,
            qf_monthly_uri_list[m_index-1], gdal.GDT_Float32, qf_nodata,
            pixel_size, 'intersection', vectorize_op=False,
            datasets_are_pre_aligned=True)

    LOGGER.info('calculating QFi')
    def qfi_sum(*qf_values):
        """sum the monthly qfis"""
        qf_sum = qf_values[0].copy()
        for index in range(1, len(qf_values)):
            qf_sum += qf_values[index]
        qf_sum[qf_values[0] == qf_nodata] = qf_nodata
        return qf_sum
    pygeoprocessing.geoprocessing.vectorize_datasets(
        qf_monthly_uri_list, qfi_sum, qfi_uri,
        gdal.GDT_Float32, qf_nodata, pixel_size, 'intersection',
        vectorize_op=False, datasets_are_pre_aligned=True)


def calculate_slow_flow(
        precip_uri_list, et0_uri_list, flow_dir_uri, lulc_uri, kc_lookup,
        alpha_m, beta_i, gamma, qfi_uri,
        recharge_uri, recharge_avail_uri, vri_uri):
    """calculate slow flow index"""




def main():
    """main entry point"""

    et0_dir = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\et0_proj"
    precip_dir = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\precip_proj"

    dem_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\DEM\fillFinalSaga.tif"
    aoi_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\Subwatershed7\subws_id7.shp"
    #aoi_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\Subwatershed1\subws_id1.shp"
    cn_table_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\cn.csv"
    rain_events_table_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\Number of events.csv"
    precip_uri_list = []
    et0_uri_list = []

    et0_dir_list = [os.path.join(et0_dir, f) for f in os.listdir(et0_dir)]
    precip_dir_list = [
        os.path.join(precip_dir, f) for f in os.listdir(precip_dir)]

    for month_index in range(1, N_MONTHS + 1):
        month_file_match = re.compile(r'.*[^\d]%d\.[^.]+$' % month_index)

        for data_type, dir_list, uri_list in [
                ('et0', et0_dir_list, et0_uri_list),
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

    output_dir = r"C:\Users\rich\Documents\delete_seasonal_water_yield_output"

    pygeoprocessing.geoprocessing.create_directories([output_dir])

    qfi_uri = os.path.join(output_dir, 'qf.tif')
    cn_uri = os.path.join(output_dir, 'cn.tif')
    lulc_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\nass_sw_lulc.tif"

    #pre align all the datasets
    precip_uri_aligned_list = [
        pygeoprocessing.geoprocessing.temporary_filename() for _ in
        range(len(precip_uri_list))]
    et0_uri_aligned_list = [
        pygeoprocessing.geoprocessing.temporary_filename() for _ in
        range(len(precip_uri_list))]

    lulc_uri_aligned = pygeoprocessing.geoprocessing.temporary_filename()
    dem_uri_aligned = pygeoprocessing.geoprocessing.temporary_filename()

    pixel_size = pygeoprocessing.geoprocessing.get_cell_size_from_uri(lulc_uri)

    LOGGER.info('Aligning and clipping dataset list')
    pygeoprocessing.geoprocessing.align_dataset_list(
        precip_uri_list + et0_uri_list + [lulc_uri, dem_uri],
        precip_uri_aligned_list + et0_uri_aligned_list +
        [lulc_uri_aligned, dem_uri_aligned],
        ['nearest'] * (len(precip_uri_list) + len(et0_uri_aligned_list) + 2),
        pixel_size, 'intersection', 0, aoi_uri=aoi_uri,
        assert_datasets_projected=True)

    calculate_quick_flow(
        precip_uri_aligned_list, rain_events_table_uri, lulc_uri_aligned,
        cn_table_uri, cn_uri, qfi_uri, output_dir)

    alpha_m = 1./12
    beta_i = 1.
    gamma = 1.
    biophysical_table_uri = r"C:\Users\rich\Documents\invest-natcap.invest-3\test\invest-data\SeasonalWaterYield\input\biophysical_Cape_Fear.csv"
    biophysical_table = pygeoprocessing.geoprocessing.get_lookup_from_table(
        biophysical_table_uri, 'lucode')

    kc_lookup = dict([
        (lucode, biophysical_table[lucode]['kc']) for lucode in
        biophysical_table])

    recharge_uri = os.path.join(output_dir, 'recharge.tif')
    recharge_avail_uri = os.path.join(output_dir, 'recharge_avail.tif')
    vri_uri = os.path.join(output_dir, 'vri.tif')

    flow_dir_uri = os.path.join(output_dir, 'flow_dir.tif')
    pygeoprocessing.routing.flow_direction_d_inf(
        dem_uri_aligned, flow_dir_uri)

    calculate_slow_flow(
        precip_uri_aligned_list, et0_uri_aligned_list, flow_dir_uri,
        lulc_uri_aligned, kc_lookup, alpha_m, beta_i, gamma, qfi_uri,
        recharge_uri, recharge_avail_uri, vri_uri)

if __name__ == '__main__':
    main()
