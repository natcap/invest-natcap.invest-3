"""GLOBIO InVEST Model"""

import os

import gdal
import numpy
import pygeoprocessing

def execute(args):
    """main execute entry point"""

    #append a _ to the suffix if it's not empty and doens't already have one
    try:
        file_suffix = args['results_suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''

    pygeoprocessing.geoprocessing.create_directories([args['workspace_dir']])

    #load the infrastructure layers from disk
    infrastructure_filenames = []
    infrastructure_nodata_list = []
    for root_directory, _, filename_list in os.walk(
            args['infrastructure_dir']):

        for filename in filename_list:
            if filename.lower().endswith(".tif"):
                infrastructure_filenames.append(
                    os.path.join(root_directory, filename))
                infrastructure_nodata_list.append(
                    pygeoprocessing.geoprocessing.get_nodata_from_uri(
                        infrastructure_filenames[-1]))

    infrastructure_nodata = -1
    infrastructure_uri = os.path.join(
        args['workspace_dir'], 'combined_infrastructure%s.tif' % file_suffix)
    out_pixel_size = pygeoprocessing.geoprocessing.get_cell_size_from_uri(
        args['lulc_uri'])

    def collapse_infrastructure_op(*infrastructure_array_list):
        """Combines all input infrastructure into a single map where if any
            pixel on the stack is 1 gets passed through, any nodata pixel
            masks out all of them"""
        nodata_mask = (
            infrastructure_array_list[0] == infrastructure_nodata_list[0])
        infrastructure_result = infrastructure_nodata_list[0] > 0
        for index in range(1, len(infrastructure_array_list)):
            current_nodata = (
                infrastructure_array_list[index] ==
                infrastructure_nodata_list[index])

            infrastructure_result = (
                infrastructure_result |
                ((infrastructure_array_list[index] > 0) & ~current_nodata))

            nodata_mask = (
                nodata_mask & current_nodata)

        return numpy.where(
            nodata_mask, infrastructure_nodata, infrastructure_result)

    pygeoprocessing.geoprocessing.vectorize_datasets(
        infrastructure_filenames, collapse_infrastructure_op,
        infrastructure_uri, gdal.GDT_Byte, infrastructure_nodata,
        out_pixel_size, "intersection", dataset_to_align_index=0,
        assert_datasets_projected=False, vectorize_op=False)

    #infrasturcutre_filenames


    #align and clip all the layers?  is there an AOI?

    #load all the infrastructure layers and make a single layer

    #calc_msa_f

    #calc_msa_i

    #calc_msa_lu

    #calc msa msa = msa_f[tail_type] * msa_lu[tail_type] * msa_i[tail_type]

