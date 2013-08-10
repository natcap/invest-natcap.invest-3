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

    def unique_pair_op(*pixel_list):
        transitions.update(zip(pixel_list, pixel_list[1:]))
        return 0

    pixel_size = raster_utils.get_cell_size_from_uri(dataset_uri_list[0])
    dataset_garbage_out_uri = raster_utils.temporary_filename()
    raster_utils.vectorize_datasets(
        dataset_uri_list, unique_pair_op, dataset_garbage_out_uri,
        gdal.GDT_Byte, 0, pixel_size, 'intersection')
    
    return transitions

def execute(args):
    transition_matrix_uri = os.path.join(args["workspace_dir"], "transition.csv")
    nodata = set([raster_utils.get_nodata_from_uri(uri) for uri in args["lulc"]])

    LOGGER.debug("Validating LULCs.")
    if len(nodata) > 1:
        msg = "The LULCs contain more than one no data value."
        LOGGER.error(msg)
        raise ValueError, msg
    nodata = list(nodata)[0]
    LOGGER.debug("No data value is %i.", nodata)


##    #It might be handy allow for a SetCategoryNames
##    dataset = gdal.Open(args["lulc"][0])
##    band = dataset.GetRasterBand(1)
##    names = band.GetCategoryNames()
##    band = None
##    dataset = None
##
##    if not names == None:
##        LOGGER.debug("Found category names: %s.", names)
##    else:
##        LOGGER.debug("No imbedded category names found.")

    LOGGER.info("Reading all transitions.")
    transitions = get_transition_set_from_uri(args["lulc"])
    if (nodata, nodata) in transitions:
        LOGGER.debug("Removing nodata transitions.")
        transitions.remove((nodata, nodata))

    LOGGER.debug("Validating transitions.")
    from_no_data_msg = "Transition from no data to LULC unsupported."
    to_no_data_msg = "Transition from LULC unsupported to no data."
    original_values = set([])
    final_values = set([])
    for transition in transitions:
        original, final = transition

        original_values.add(int(original))
        final_values.add(int(final))
        
        if original == nodata:
            if not final == nodata:
                LOGGER.error(from_no_data_msg)
                raise ValueError, from_no_data_msg
        elif final == nodata:
            LOGGER.error(to_no_data_msg)
            raise ValueError, to_no_data_msg
    transitions = set(transitions)

    LOGGER.info("Creating transition matrix.")
    original_values = list(original_values)
    final_values = list(final_values)
    original_values.sort()
    final_values.sort()
    transition_matrix = open(transition_matrix_uri, 'w')
    transition_matrix.write("ID,,")
    transition_matrix.write(",".join([str(value) for value in final_values]))

    transition_matrix.write("\n,Name")
    labels_dict = {}
    #This will cause problems if the carbon table is missing more than one label.
    if args["labels"] != "":
        LOGGER.info("Reading category names from table.")
        labels_dict = raster_utils.get_lookup_from_csv(args["labels"], args["lulc_id"])
        for lulc_id in final_values:
            transition_matrix.write(",%s" % labels_dict[lulc_id][args["lulc_name"]])
    else:
        transition_matrix.write(",".join([""] * (len(final_values)+1)))
    
    for original in original_values:
        transition_matrix.write("\n%i" % original)
        if original in labels_dict:
            transition_matrix.write(",%s" % labels_dict[original][args["lulc_name"]])
        else:
            transition_matrix.write(",")
            
        for final in final_values:
            if original == final:
                transition_matrix.write(",%i" % 0)
            elif (original, final) in transitions:
                transition_matrix.write(",")
            else:
                transition_matrix.write(",%i" % 0)
    transition_matrix.close()
