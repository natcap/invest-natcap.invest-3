import os

from osgeo import gdal

from invest_natcap import raster_utils

def reclassify_lulc_samp_cur():
    # I'm using Hydrological Soil Group A, from table 10.4 in the Flood Mitigation
    # user's guide.  Assuming pixel size of 900 m^2.
    reclass = {
        1: 61,
        2: 61,
        3: 61,
        4: 61,
        6: 89,
        7: 81,
        8: 81,
        11: 40,
        16: 55,
        18: 76,
        20: 76,
        21: 74,
        24: 50,
        29: 100,  # non-vegetated channel (water)
        32: 100,  # order 5-7 stream
        33: 100,  # permanent lentic water
        39: 50,
        49: 49,
        51: 46,
        52: 36,
        53: 30,
        54: 30,
        55: 40,
        56: 35,
        57: 35,
        58: 35,
        59: 35,
        60: 35,
        61: 35,
        62: 35,
        66: 35,
        67: 55,
        68: 72,
        71: 72,
        72: 65,
        73: 50,
        74: 72,
        75: 72,
        76: 72,
        78: 72,
        79: 72,
        80: 72,
        81: 72,
        82: 72,
        83: 72,
        84: 72,
        85: 72,
        86: 48,
        87: 28,
        88: 77,
        89: 100, # flooded/marsh
        90: 72,
        91: 72,
        92: 39,
        93: 35,
        95: 35
    }

    # setting the lulc_samp_cur path relative to the invest-3 root
    lulc_path = os.path.join('test', 'data', 'base_data', 'terrestrial',
        'lulc_samp_cur', 'hdr.adf')
    output_path = 'curve_numbers.tif'

    raster_utils.reclassify_by_dictionary(gdal.Open(lulc_path), reclass,
        output_path, 'GTiff', 255, gdal.GDT_Float32)

if __name__ == '__main__':
    reclassify_lulc_samp_cur()
