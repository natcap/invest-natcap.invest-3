import logging
from osgeo import gdal, ogr
import numpy
import scipy.ndimage

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('scenario_generator')

def filter_fragments(input_uri, value, min_size, count, output_uri, replace=None):
    #clump and sieve
    LOGGER.debug("Filtering patches smaller than %i from %s.", min_size, input_uri)

    src_ds = gdal.Open(input_uri)
    src_band = src_ds.GetRasterBand(1)
    src_array = src_band.ReadAsArray()

    driver = gdal.GetDriverByName("GTiff")
    driver.CreateCopy(output_uri, src_ds, 0 )

    dst_ds = gdal.Open(output_uri, 1)
    dst_band = dst_ds.GetRasterBand(1)
    dst_array = numpy.copy(src_array)

    if replace == None:
        replace = dst_band.GetNoDataValue()

    suitability_values = numpy.unique(src_array)
    if suitability_values[0] == 0:
        suitability_values = suitability_values[1:]

    #8 connectedness preferred, 4 connectedness allowed
    mask = src_array == value # You get a mask with the polygons only
    ones_in_mask = numpy.sum(mask)
    print('Processing value' + str(value) + ' (found ' + \
    str(ones_in_mask) + ' among ' + str(mask.size) + ')')
    label_im, nb_labels = scipy.ndimage.label(mask)
    src_array[mask] = 1
    fragment_sizes = scipy.ndimage.sum(mask, label_im, range(nb_labels + 1))
    fragment_labels = numpy.array(range(nb_labels + 1))
    print('Labels', nb_labels, fragment_sizes)
    assert fragment_sizes.size == len(fragment_labels)
    small_fragment_mask = numpy.where(fragment_sizes < min_size)
    small_fragment_sizes = fragment_sizes[small_fragment_mask]
    small_fragment_labels = fragment_labels[small_fragment_mask]
    print('small fragment count', small_fragment_sizes.size)
    combined_small_fragment_size = numpy.sum(small_fragment_sizes)
    print('fragments to remove', combined_small_fragment_size)
    print('small fragment sizes', small_fragment_sizes)
    print('small fragment labels', small_fragment_labels)
    #print('large_fragments', large_fragments.size, large_fragments)
    removed_pixels = 0
    for label in small_fragment_labels[1:]:
        pixels_to_remove = numpy.where(label_im == label)
        dst_array[pixels_to_remove] = replace
        removed_pixels += pixels_to_remove[0].size
        print('removed ' + str(pixels_to_remove[0].size) + \
        ' pixels with label ' + str(label) + ', total = ' + \
        str(removed_pixels))
    message = 'Ones in mask = ' + str(combined_small_fragment_size) + \
    ', pixels removed = ' + str(removed_pixels)
    assert removed_pixels == combined_small_fragment_size, message

    dst_band.WriteArray(dst_array)

if __name__ == "__main__":
    input_uri = "/home/mlacayo/workspace/data/ScenarioGenerator/input/landcover.tif"
    min_size = 2
    output_uri = "/home/mlacayo/workspace/data/ScenarioGenerator/output/despeckled.tif"
    value = 10
    replace = 1
    count = 50

    filter_fragments(input_uri, value, min_size, count, output_uri, replace)
