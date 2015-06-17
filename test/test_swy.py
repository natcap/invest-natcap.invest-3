"""Standalone test of test_swy"""

import pprint
import hashlib
import os

import pygeoprocessing
#import invest_natcap.seasonal_water_yield.seasonal_water_yield
import seasonal_water_yield_core
#import ndr_core
#import scenic_quality_cython_core

args = {
        u'alpha_m': u'1/12',
        u'aoi_uri': u'C:/Users/rich/Documents/Dropbox/SeasonalWaterYield/input/Subwatershed7/subws_id7.shp',
#        u'aoi_uri': u'C:/Users/rich/Documents/Dropbox/SeasonalWaterYield/input/Subwatershed6/subws_id6.shp',
        u'beta_i': u'1.0',
        u'biophysical_table_uri': u'C:/Users/rich/Documents/Dropbox/SeasonalWaterYield/input/biophysical_Cape_Fear.csv',
        u'cn_table_uri': u'C:/Users/rich/Documents/Dropbox/SeasonalWaterYield/input/cn.csv',
        u'dem_uri': u'C:/Users/rich/Documents/Dropbox/SeasonalWaterYield/input/DEM/fillFinalSaga.tif',
        u'et0_dir': u'C:\\Users\\rich\\Documents\\SeasonalWaterYield\\input\\et0_proj',
        u'gamma': u'1.0',
        u'lulc_uri': u'C:\\Users\\rich\\Documents\\SeasonalWaterYield\\input\\nass_sw_lulc.tif',
        u'precip_dir': u'C:/Users/rich/Documents/Dropbox/SeasonalWaterYield/input/precip_proj',
        u'rain_events_table_uri': u'C:/Users/rich/Documents/Dropbox/SeasonalWaterYield/input/Number of events.csv',
        u'threshold_flow_accumulation': u'200',
        u'workspace_dir': u'C:\\Users\\rich/Documents/delete_swy_script',
        u'results_suffix': u'',
}

def md5_for_filename(filename, block_size=2**20):
    """Returns an MD5 hash of a filename"""
    file_handle = open(filename, 'rb')
    md5 = hashlib.md5()
    while True:
        data = file_handle.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()

def compare_directories(directory_test, directory_base):
    """Recursively compares the two directories to make sure they have the
        same filenames and the files are the same contents.

        directory_test (string) - directory to compare against the test
        directory_base (string) - base 'truth' directory

        returns a list of tuples showing which files are different and an
            error code as to why"""
    difference_list = []
    for root, _, files in os.walk(directory_base):
        for filename in files:
            try:
                relpath = os.path.relpath(root, directory_base)
                test_filename = os.path.join(directory_test, relpath, filename)
                base_filename = os.path.join(root, filename)
                test_md5 = md5_for_filename(test_filename)
                base_md5 = md5_for_filename(base_filename)
                if test_md5 != base_md5:
                    difference_list.append(
                        (base_filename, test_filename, base_md5, test_md5))
            except IOError:
                difference_list.append((base_filename, 'current not found'))
    return difference_list

if __name__ == '__main__':
    dem_uri_aligned = r"C:\Users\rich\Documents\delete_base_sw_ui_user_defined_recharge_layer2\aligned_dem.tif"
    pygeoprocessing.create_directories([r"C:\Users\Rich\Documents\delete_sf_debug"])
    for data_dir in ['delete_base_sw_ui_user_defined_recharge_layer2', 'delete_base_sw_ui']:
        recharge_avail_uri = r"C:\Users\rich\Documents\%s\recharge_avail.tif" % data_dir #OKAY (DOUBLE)
        r_sum_avail_uri = r"C:\Users\rich\Documents\%s\r_sum_avail.tif" % data_dir #SLIGHTLY OFF, BUT MAY BE BECAUSE OF MISALIGNMENT (NODATA VALUES ARE DIFFERENT -1 for recharge -99999 for base)
        r_sum_avail_pour_uri = r"C:\Users\rich\Documents\%s\r_sum_avail_pour.tif" % data_dir #OFF BY ABSOLUTE VALUES OF HUNDREDS TO THOUSANDS; SEEMS SMALL IN LARGER SCOPE
        outflow_direction_uri = r"C:\Users\rich\Documents\%s\outflow_direction.tif" % data_dir #SAME
        outflow_weights_uri = r"C:\Users\rich\Documents\%s\outflow_weights.tif" % data_dir #SAME
        stream_uri = r"C:\Users\rich\Documents\%s\stream.tif" % data_dir #SAME
        sf_uri = r"C:\Users\rich\Documents\delete_sf_debug\sf_recharge_%s.tif" % data_dir
        sf_down_uri = r"C:\Users\rich\Documents\delete_sf_debug\sf_down_%s.tif" % data_dir
        seasonal_water_yield_core.route_sf(
            dem_uri_aligned, recharge_avail_uri, r_sum_avail_uri,
            r_sum_avail_pour_uri, outflow_direction_uri, outflow_weights_uri,
            stream_uri, sf_uri, sf_down_uri)


#    invest_natcap.seasonal_water_yield.seasonal_water_yield.execute(args)
#    DIRECTORY_BASE = r"C:\Users\rich\Documents\delete_base_sw"
#    print "Regression testing result"
#    difference_list =  compare_directories(args['workspace_dir'], DIRECTORY_BASE)
#    if len(difference_list) > 0:
#        print "These files don't match: "
#        pprint.pprint(difference_list)
#    else:
#        print "Everything matches!"
