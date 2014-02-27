import os
import math
import shutil
import disk_sort
import struct
import operator
import logging
from decimal import Decimal
from fractions import Fraction

import numpy
from scipy.linalg import eig
import scipy.ndimage

from osgeo import gdal, ogr

from invest_natcap import raster_utils


logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('scenario_generator')


def calculate_weights(arr, rounding=4):
    
   PLACES = Decimal(10) ** -(rounding)
   
   # get eigenvalues and vectors
   evas, eves = eig(arr)

   # get primary eigenvalue and vector
   eva = max(evas)
   eva_idx = evas.tolist().index(eva)
   eve = eves.take((eva_idx,), axis=1)

   # priority vector = normalized primary eigenvector

   normalized = eve / sum(eve)

   # turn into list of real part values
   vector = [abs(e[0]) for e in normalized]

   # return nice rounded Decimal values with labels
   return [ Decimal( str(v) ).quantize(PLACES) for v in vector ]

def calculate_priority(table_uri):
    table = [line.strip().split(",") for line in open(table_uri).readlines()]
    id_index = table[0].index("Id")

    cover_id_list = [row[id_index] for row in table]
    cover_id_list.pop(0)

    cover_id_index_list = [table[0].index(cover_id) for cover_id in cover_id_list]

    matrix = numpy.zeros((len(cover_id_list),len(cover_id_list)))

    for row in range(len(cover_id_list)):
       for col in range(row+1):
            matrix[row][col] = float(table[row+1][cover_id_index_list[col]])
            matrix[col][row] = 1 / matrix[row][col]

    cover_id_list = [int(cover_id) for cover_id in cover_id_list]
    return dict(zip(cover_id_list, calculate_weights(matrix, 4)))

def calculate_distance_raster_uri(dataset_in_uri, dataset_out_uri, cell_size = None, max_distance = None):
    if cell_size == None:
       cell_size = raster_utils.get_cell_size_from_uri(dataset_in_uri)

    memory_array = raster_utils.load_memory_mapped_array(dataset_in_uri, raster_utils.temporary_filename())

    memory_array = scipy.ndimage.morphology.distance_transform_edt(memory_array) * cell_size

    nodata = raster_utils.get_nodata_from_uri(dataset_in_uri)

##    if max_distance != None:
##        memory_array[memory_array > max_distance] = nodata
    
    raster_utils.new_raster_from_base_uri(dataset_in_uri, dataset_out_uri, 'GTiff', nodata, gdal.GDT_Float32)

    dataset_out = gdal.Open(dataset_out_uri, 1)
    band = dataset_out.GetRasterBand(1)
    band.WriteArray(memory_array)

    band = None
    dataset_out = None


shapeTypes= {0: "Null Shape", 1: "Point", 3: "PolyLine", 5: "Polygon",
             8: "MultiPoint", 11: "PointZ", 13: "PolyLineZ",
             15: "PolygonZ", 18: "MultiPointZ", 21: "PointM",
             23: "PolyLineM", 25: "PolygonM", 28: "MultiPointM",
             31: "MultiPatch"}

def get_geometry_type_from_uri(datasource_uri):
    datasource = open(datasource_uri, 'r')
    datasource.seek(32)
    shape_type ,= struct.unpack('<i',datasource.read(4))
    datasource.close()

    return shape_type

def sieve_dataset_uri(dataset_in_uri, dataset_out_uri, mask_op, size_op, replacement):
    src_ds = gdal.Open(dataset_in_uri)

    gdal.GetDriverByName("GTiff").CreateCopy(dataset_out_uri, src_ds, 0 )

    src_band = src_ds.GetRasterBand(1)
    src_array = src_band.ReadAsArray()

    dst_ds = gdal.Open(dataset_out_uri, 1)
    dst_band = dst_ds.GetRasterBand(1)
    dst_array = dst_band.ReadAsArray()

    mask = mask_op(src_array)
    label_im, nb_labels = scipy.ndimage.label(mask)
    sizes = scipy.ndimage.sum(mask, label_im, range(nb_labels + 1))
    mask_size = size_op(sizes)
    remove_pixel = mask_size[label_im]
    dst_array[remove_pixel] = replacement
    dst_band.WriteArray(dst_array)

    dst_band = None
    dst_ds = None
    src_band = None
    src_ds = None

def get_transition_set_count_from_uri(dataset_uri_list):
    cell_size = raster_utils.get_cell_size_from_uri(dataset_uri_list[0])
    lulc_nodata = int(raster_utils.get_nodata_from_uri(dataset_uri_list[0]))
    nodata = 0
    
    #reclass rasters to compact bit space
    lulc_codes = set()
    unique_raster_values_count = {}
    
    for dataset_uri in dataset_uri_list:
        unique_raster_values_count[dataset_uri] = raster_utils.unique_raster_values_count(dataset_uri)
        lulc_codes.update(unique_raster_values_count[dataset_uri].keys())
        
    lulc_codes = list(lulc_codes)
    lulc_codes.sort()

    if len(lulc_codes) < 2 ** 8:
        data_type = gdal.GDT_UInt16
        shift = 8
    elif len(lulc_codes) < 2 ** 16:
        data_type = gdal.GDT_UInt32
        shift = 16
    else:
        raise ValueError, "Too many LULC codes."

    #renumber and reclass rasters
    reclass_orig_dict = dict(zip(lulc_codes,range(1,len(lulc_codes)+1)))

    reclass_dest_dict = {}
    for key in reclass_orig_dict:
        reclass_dest_dict[key] = reclass_orig_dict[key] << shift

    def add_op(orig, dest):
        return orig + dest

    counts={}
    for i in range(len(dataset_uri_list)-1):
        orig_uri = raster_utils.temporary_filename()
        dest_uri = raster_utils.temporary_filename()
        multi_uri = raster_utils.temporary_filename()

        #reclass orig values
        raster_utils.reclassify_dataset_uri(dataset_uri_list[i],
                                            reclass_orig_dict,
                                            orig_uri,
                                            data_type,
                                            nodata,
                                            exception_flag="values_required")

        #reclass dest values
        raster_utils.reclassify_dataset_uri(dataset_uri_list[i+1],
                                            reclass_dest_dict,
                                            dest_uri,
                                            data_type,
                                            nodata,
                                            exception_flag="values_required")

        #multiplex orig with dest
        raster_utils.vectorize_datasets([orig_uri, dest_uri],
                                        add_op,
                                        multi_uri,
                                        data_type,
                                        nodata,
                                        cell_size,
                                        "union")
    
        #get unique counts
        counts[i]=raster_utils.unique_raster_values_count(multi_uri, False)

    restore_classes = {}
    for key in reclass_orig_dict:
        restore_classes[reclass_orig_dict[key]] = key
    restore_classes[nodata] = lulc_nodata

    LOGGER.debug("Decoding transition table.")
    transitions = {}
    for key in counts:
        transitions[key]={}
        for k in counts[key]:
            try:
                orig = restore_classes[k % (2**shift)]
            except KeyError:
                orig = lulc_nodata
            try:
                dest = restore_classes[k >> shift]
            except KeyError:
                dest = lulc_nodata
                
            try:
                transitions[key][orig][dest] = counts[key][k]
            except KeyError:
                transitions[key][orig] = {dest : counts[key][k]}

    return unique_raster_values_count, transitions

def generate_chart_html(cover_dict):
    html = "\n<TABLE BORDER=1>"
    html += "\n<TR><TD>Id</TD><TD>Before</TD><TD>After</TD></TR>"
    cover_id_list = cover_dict.keys()
    cover_id_list.sort()

    for cover_id in cover_id_list:
       html += "\n<TR><TD>%i</TD><TD>%i</TD><TD>%i</TD></TR>" % (cover_id,
                                                                 cover_dict[cover_id][0],
                                                                 cover_dict[cover_id][1])

    html += "\n<TABLE>"

    return html

def filter_fragments(input_uri, size, output_uri):
    shutil.copy(input_uri, output_uri)
##    #clump and sieve
##    for cover_id in transition_dict:
##        if transition_dict[cover_id][args["patch_field"]] > 0 and cover_id in suitability_dict:
##            LOGGER.info("Filtering patches from %i.", cover_id)
##            size = int(math.ceil(transition_dict[cover_id][args["patch_field"]] / cell_size))
##
##            LOGGER.debug("Filtering patches smaller than %i from %i.", size, cover_id)
##
##            src_ds = gdal.Open(suitability_dict[cover_id])
##            src_band = src_ds.GetRasterBand(1)
##            src_array = src_band.ReadAsArray()
##
##            dst_uri = os.path.join(workspace, "intermediate/filtered_%i.tif" % cover_id)
##            driver.CreateCopy(dst_uri, src_ds, 0 )
##
##            dst_ds = gdal.Open(dst_uri, 1)
##            dst_band = dst_ds.GetRasterBand(1)
##            dst_array = dst_band.ReadAsArray()
##
##            suitability_values = numpy.unique(src_array)
##            if suitability_values[0] == 0:
##               suitability_values = suitability_values[1:]
##
##            #8 connectedness preferred, 4 connectedness allowed
##            #dst_array = numpy.zeros_like(dst_array)
##            for value in [suitability_values[0]]:
##               mask = src_array == value # You get a mask with the polygons only
##               label_im, nb_labels = scipy.ndimage.label(mask) # Use the mask to label the polygons
##               src_array[mask] = 1
##               sizes = scipy.ndimage.sum(mask, label_im, range(nb_labels + 1)) # Compute the polygon area in pixels
##               print size
##               print sizes
##               size_mask = sizes < size # Keep cells from polygons smaller than 1000 cells in size_mask
##               remove_cells = size_mask[label_im] # Extract all the cells from the raster that belong to small polygons
##               #label_im[remove_cells] = 0 # Erase these cells by overriding their value with the value 0.
##               dst_array[remove_cells] = 0
##
##            dst_band.WriteArray(dst_array)
##            dst_band = None
##            dst_ds = None
##            src_band = None
##            src_ds = None

def execute(args):
    ###
    #overiding, non-standard field names
    ###

    #transition table fields
    args["transition_id"] = "Id"
    args["percent_field"] = "Percent Change"
    args["area_field"] = "Area Change"
    args["priority_field"] = "Priority"
    args["proximity_field"] = "Proximity"
    args["proximity_weight"] = "0.3"
    args["patch_field"] = "Patch ha"

    #factors table fields
    args["suitability_id"] =  "Id"
    args["suitability_layer"] = "Layer"
    args["suitability_weight"] = "Wt"
    args["suitability_field"] = "Suitfield"
    args["distance_field"] = "Dist"

    args["suitability_cover_id"] = "Cover ID"
    
    ###
    #get parameters, set outputs
    ###
    workspace = args["workspace_dir"]
    landcover_uri = args["landcover"]

    intermediate_dir = "intermediate"

    if not os.path.exists(os.path.join(workspace, intermediate_dir)):
        os.makedirs(os.path.join(workspace, intermediate_dir))

    proximity_weight = float(args["proximity_weight"])

    #it might be better to just check if factors being used
    try:
       physical_suitability_weight = float(args["weight"])
    except KeyError:
       physical_suitability_weight = 0.5


##    def mask_op(value):
##       """
##       Exclusion mask. You specify what you want to mask out, i.e. not change.
##       """
##       return value != 6
##
##    def size_op(value):
##       return value < 2
##
##    sieve_dataset_uri(landcover_uri, os.path.join(workspace, "filter.tif"), mask_op, size_op, 0)
##
##    return
   

    ##output file names
    #absolute paths
    landcover_resample_uri = os.path.join(workspace, "resample.tif")

    landcover_transition_uri = os.path.join(workspace,"transitioned.tif")
    override_dataset_uri = os.path.join(workspace,"override.tif")
    landcover_htm_uri = os.path.join(workspace,"landcover.htm")

    raster_utils.create_directories([workspace])

    #relative paths, or with patterned name
    transition_name = os.path.join(intermediate_dir, "transition_%i.tif")
    suitability_name = os.path.join(intermediate_dir, "%s_%s.tif")
    normalized_name = os.path.join(intermediate_dir, "%s_%s_norm.tif")
    combined_name = os.path.join(intermediate_dir, "factors_%s.tif")
    constraints_name = os.path.join(intermediate_dir, "constraints.tif")
    factors_name = os.path.join(intermediate_dir, "suitability_%s.tif")
    cover_name = os.path.join(intermediate_dir, "cover_%i.tif")
    proximity_name = os.path.join(intermediate_dir, "proximity_%s.tif")
    normalized_proximity_name = os.path.join(intermediate_dir, "proximity_norm_%s.tif")
    adjusted_suitability_name = os.path.join(intermediate_dir, "adjusted_suitability_%s.tif")

    scenario_name = "scenario.tif"

    ###
    #constants
    ###
    raster_format = "GTiff"
    transition_type = gdal.GDT_Int16
    transition_nodata = -1

    #value to multiply transition matrix entries (ie covert 10 point scale to 100 point scale)
    transition_scale = 10
    distance_scale = 100

    suitability_nodata = 0
    suitability_type = gdal.GDT_Int16

    def suitability_op(trans, suit):
        return ((1 - physical_suitability_weight) * trans)\
               + (physical_suitability_weight * suit)

    ds_type = "GTiff"
    driver = gdal.GetDriverByName(ds_type)
    
    ###
    #validate data
    ###
    #raise warning if nothing is going to happen
    if not any([args["calculate_transition"],
                args["calculate_factors"],
                args["override_layer"]]):
        msg = "You must select at least one of the following: specify transitions, use factors, or override layer."
        LOGGER.error(msg)
        raise ValueError, msg

    ##transition table validation
    #raise error if transition table provided, but not used
    if args["transition"] and not(args["calculate_transition"] or args["calculate_factors"]):
        msg = "Transition table provided but not used."
        LOGGER.error(msg)
        raise ValueError, msg
      
    if args["calculate_transition"] or args["calculate_factors"]:
        #load transition table
        transition_dict = raster_utils.get_lookup_from_csv(args["transition"], args["transition_id"])
        
        #raise error if LULC contains cover id's not in transition table
        landcover_count_dict = raster_utils.unique_raster_values_count(landcover_uri)
        missing_lulc = set(landcover_count_dict).difference(transition_dict.keys())
        if len(missing_lulc) > 0 :
            missing_lulc = list(missing_lulc)
            missing_lulc.sort()
            mising_lulc = ", ".join([str(l) for l in missing_lulc])
            msg = "Missing suitability information for cover(s) %s." % missing_lulc
            LOGGER.error(msg)
            raise ValueError, msg

        for cover_id in transition_dict:
            #raise error if percent change for new LULC           
            if (transition_dict[cover_id][args["percent_field"]] > 0) and not (cover_id in landcover_count_dict):
                msg = "Cover %i does not exist in LULC and therefore cannot have a percent change." % cover_id
                LOGGER.error(msg)
                raise ValueError, msg

            #raise error if change by percent and area both specified
            if (transition_dict[cover_id][args["percent_field"]] > 0) and (transition_dict[cover_id][args["area_field"]] > 0):
                msg = "Cover %i cannot have both an increase by percent and area." % cover_id
                LOGGER.error(msg)
                raise ValueError, msg
    
    ##factor parameters validation
    if args["calculate_factors"]:
        pass
        #error if overall physical weight not in [0, 1] range
      
        ##factor table validation
        #if polygon no distance field allowed
        #if point or line, integer distance field only
        #error if same factor twice for same coverage

    ###
    #resample, align and rasterize data
    ###
    if args["calculate_priorities"]:
        LOGGER.info("Calculating priorities.")
        priorities_dict = calculate_priority(args["priorities_csv_uri"])
        
    #check geographic extents, projections

    #validate resampling size
    if args["resolution"] != "":
       if args["resolution"] < raster_utils.get_cell_size_from_uri(landcover_uri):
          msg = "The analysis resolution cannot be smaller than the input."
          LOGGER.error(msg)
          raise ValueError, msg

       else:
          LOGGER.info("Resampling land cover.")
          #gdal.GRA_Mode might be a better resample method, but requires GDAL >= 1.10.0
          raster_utils.resample_dataset(landcover_uri, args["resolution"], landcover_resample_uri, gdal.GRA_NearestNeighbour)
          landcover_uri = landcover_resample_uri

    cell_size = raster_utils.get_cell_size_from_uri(landcover_uri)

    suitability_transition_dict = {}
   
    if args["calculate_transition"]:
        for next_lulc in transition_dict:
            this_uri = os.path.join(workspace, transition_name % next_lulc)
            #construct reclass dictionary
            reclass_dict = {}
            all_zeros = True
            for this_lulc in transition_dict:
                value = int(transition_dict[this_lulc][str(next_lulc)])
                reclass_dict[this_lulc] = value * transition_scale
                all_zeros = all_zeros and (value == 0)

            if not all_zeros:
                #reclass lulc by reclass_dict
                raster_utils.reclassify_dataset_uri(landcover_uri,
                                                    reclass_dict,
                                                    this_uri,
                                                    transition_type,
                                                    suitability_nodata,
                                                    exception_flag = "values_required") 

                #changing nodata value so 0's no longer nodata
                dataset = gdal.Open(this_uri, 1)
                band = dataset.GetRasterBand(1)
                nodata = band.SetNoDataValue(transition_nodata)
                dataset = None

                suitability_transition_dict[next_lulc] = this_uri
                      
    suitability_factors_dict = {}
    if args["calculate_factors"]:
        factor_dict = raster_utils.get_lookup_from_csv(args["suitability"], args["suitability_id"])
        factor_uri_dict = {}
        factor_folder = args["suitability_folder"]

        if args["factor_inclusion"]:
           option_list=["ALL_TOUCHED=TRUE"]
        else:
           option_list = ["ALL_TOUCHED=FALSE"]


        for factor_id in factor_dict:
            factor = factor_dict[factor_id][args["suitability_layer"]]
            factor_stem, _ = os.path.splitext(factor)
            suitability_field_name = factor_dict[factor_id][args["suitability_field"]]
            distance = factor_dict[factor_id][args["distance_field"]]

            cover_id = int(factor_dict[factor_id][args["suitability_cover_id"]])
            weight = int(factor_dict[factor_id][args["suitability_weight"]])
            
            LOGGER.debug("Found reference to factor (%s, %s, %s) for cover %i.", factor_stem, suitability_field_name, distance, cover_id)
            if not (factor_stem, suitability_field_name, distance) in factor_uri_dict:
                factor_uri = os.path.join(factor_folder, factor)
                if not os.path.exists(factor_uri):
                   msg = "Missing file %s." % factor_uri
                   LOGGER.error(msg)
                   raise ValueError, msg

                shape_type = get_geometry_type_from_uri(factor_uri)
                LOGGER.debug("Processing %s.", shapeTypes[shape_type])
                
                if shape_type in [5, 15, 25, 31]: #polygon
                   LOGGER.info("Rasterizing %s using sutibility field %s.", factor_stem, suitability_field_name)
                   ds_uri = os.path.join(workspace, suitability_name % (factor_stem, suitability_field_name))

                   burn_value = [0]
                   suitability_field = ["ATTRIBUTE=%s" % suitability_field_name]
                   gdal_format = gdal.GDT_Float64
                   raster_utils.new_raster_from_base_uri(landcover_uri, ds_uri, raster_format, transition_nodata, gdal_format, fill_value = 0)
                   raster_utils.rasterize_layer_uri(ds_uri, factor_uri, burn_value, option_list=option_list + suitability_field)

                   factor_uri_dict[(factor_stem, suitability_field_name, distance)] = ds_uri

                elif shape_type in [1, 3, 8, 11, 13, 18, 21, 23, 28]: #point or line
                   distance = int(distance)

                   ds_uri = raster_utils.temporary_filename()
                   distance_uri = raster_utils.temporary_filename()
                   fdistance_uri = os.path.join(workspace, suitability_name % (factor_stem, distance))
                   normalized_uri = os.path.join(workspace, normalized_name % (factor_stem, distance))
                   
                   burn_value = [0]
                   LOGGER.info("Buffering rasterization of %s to distance of %i.", factor_stem, distance)
                   gdal_format = gdal.GDT_Byte
                   raster_utils.new_raster_from_base_uri(landcover_uri, ds_uri, raster_format, 1, gdal_format)

                   raster_utils.rasterize_layer_uri(ds_uri, factor_uri, burn_value, option_list)

                   calculate_distance_raster_uri(ds_uri, distance_uri)

                   def threshold(value):
                       if value > distance:
                           return transition_nodata
                       return value

                   raster_utils.vectorize_datasets([distance_uri],
                                                   threshold,
                                                   fdistance_uri,
                                                   raster_utils.get_datatype_from_uri(distance_uri),
                                                   transition_nodata,
                                                   cell_size,
                                                   "union")

                   minimum, maximum, _, _ = raster_utils.get_statistics_from_uri(fdistance_uri)

                   def normalize_op(value):
                       if value == transition_nodata:
                           return suitability_nodata
                       else:
                           return ((distance_scale - 1) \
                                   - (((value - minimum) \
                                       / float(maximum - minimum)) \
                                      * (distance_scale - 1))) \
                                      + 1

                   raster_utils.vectorize_datasets([fdistance_uri],
                                                   normalize_op,
                                                   normalized_uri,
                                                   transition_type,
                                                   transition_nodata,
                                                   cell_size,
                                                   "union")

                   factor_uri_dict[(factor_stem, suitability_field_name, distance)] = normalized_uri

                else:
                   raise ValueError, "Invalid geometry type %i." % shape_type

            else:
               LOGGER.debug("Skipping already processed suitability layer.")

            LOGGER.debug("Adding factor (%s, %s, %s) to cover %i suitability list.", factor_stem, suitability_field_name, distance, cover_id)
            if cover_id in suitability_factors_dict:
                suitability_factors_dict[cover_id].append((factor_uri_dict[(factor_stem, suitability_field_name, distance)], weight))
            else:
                suitability_factors_dict[cover_id] = [(factor_uri_dict[(factor_stem, suitability_field_name, distance)], weight)]

        for cover_id in suitability_factors_dict:
           if len(suitability_factors_dict[cover_id]) > 1:
              LOGGER.info("Combining factors for cover type %i.", cover_id)
              ds_uri = os.path.join(workspace, combined_name % cover_id)

              uri_list, weights_list = apply(zip, suitability_factors_dict[cover_id])
              
              total = float(sum(weights_list))
              weights_list = [weight / total for weight in weights_list]
              
              def weighted_op(*values):
                  return sum([ v * w for v, w in zip(values, weights_list)])

              raster_utils.vectorize_datasets(uri_list,
                                              weighted_op,
                                              ds_uri,
                                              suitability_type,
                                              transition_nodata,
                                              cell_size,
                                              "union")

              suitability_factors_dict[cover_id] = ds_uri

    suitability_dict = {}
    if args["calculate_transition"]:
        suitability_dict = suitability_transition_dict
        if args["calculate_factors"]:
           for cover_id in suitability_factors_dict:
              if cover_id in suitability_dict:
                 LOGGER.info("Combining suitability for cover %i.", cover_id)
                 ds_uri = os.path.join(workspace, factors_name % cover_id)
                 raster_utils.vectorize_datasets([suitability_transition_dict[cover_id],
                                                  suitability_factors_dict[cover_id]],
                                                 suitability_op,
                                                 ds_uri,
                                                 transition_type,
                                                 transition_nodata,
                                                 cell_size,
                                                 "union")
                 suitability_dict[cover_id] = ds_uri
              else:
                  suitability_dict[cover_id] = suitability_factors_dict[cover_id]
    elif args["calculate_factors"]:
        suitability_dict = suitability_factors_dict

    #clump and sieve
    for cover_id in transition_dict:
        if transition_dict[cover_id][args["patch_field"]] > 0 and cover_id in suitability_dict:
            LOGGER.info("Filtering patches from %i.", cover_id)
            size = int(math.ceil(transition_dict[cover_id][args["patch_field"]] / cell_size))

            LOGGER.debug("Filtering patches smaller than %i from %i.", size, cover_id)

            input_uri = os.path.join(workspace, adjusted_suitability_name % cover_id)
            basename, ext = os.path.splitext(input_uri)
            output_uri = basename + '_filtered' + ext
            print('input_uri', input_uri, 'output_uri', output_uri)
            filter_fragments(input_uri, size, output_uri)
            suitability_dict[cover_id] = output_uri

    ###
    #compute intermediate data if needed
    ###

    #contraints raster (reclass using permability values, filters on clump size)
    if args["calculate_constraints"]:
        LOGGER.info("Rasterizing constraints.")
        constraints_uri = args["constraints"]
        constraints_field_name = args["constraints_field"]
        constraints_ds_uri = os.path.join(workspace, constraints_name)
        option_list = ["ALL_TOUCHED=FALSE"]
        burn_value = [0]
        constraints_field = ["ATTRIBUTE=%s" % constraints_field_name]
        gdal_format = gdal.GDT_Float64
        raster_utils.new_raster_from_base_uri(landcover_uri, constraints_ds_uri, raster_format, transition_nodata, gdal_format, fill_value = 1)
        raster_utils.rasterize_layer_uri(constraints_ds_uri, constraints_uri, burn_value, option_list=option_list + constraints_field)

    else:
        LOGGER.info("Constraints not included.")

    proximity_dict = {}
    if args["calculate_proximity"]:
        LOGGER.info("Calculating proximity.")
        cover_types = transition_dict.keys()
        for cover_id in transition_dict:
           if transition_dict[cover_id][args["proximity_field"]] > 0 and cover_id in suitability_dict:
              distance = int(transition_dict[cover_id][args["proximity_field"]])
              LOGGER.info("Calculating proximity for %i.", cover_id)
              reclass_dict = dict(zip(cover_types, [1] * len(cover_types)))
              reclass_dict[cover_id] = 0

              ds_uri = os.path.join(workspace, cover_name % cover_id)
              distance_uri = raster_utils.temporary_filename()
              fdistance_uri = os.path.join(workspace, proximity_name % cover_id)
              normalized_uri = os.path.join(workspace, normalized_proximity_name % cover_id)
              
              raster_utils.reclassify_dataset_uri(landcover_uri,
                                                  reclass_dict,
                                                  ds_uri,
                                                  transition_type,
                                                  transition_nodata,
                                                  exception_flag = "values_required") 

              calculate_distance_raster_uri(ds_uri, distance_uri)

              def threshold(value):
                  if value > distance:
                      return transition_nodata
                  return value
 
              raster_utils.vectorize_datasets([distance_uri],
                                              threshold,
                                              fdistance_uri,
                                              raster_utils.get_datatype_from_uri(distance_uri),
                                              transition_nodata,
                                              cell_size,
                                              "union")

              minimum, maximum, _, _ = raster_utils.get_statistics_from_uri(fdistance_uri)

              def normalize_op(value):
                  if value == transition_nodata:
                      return suitability_nodata
                  else:
                      return ((distance_scale - 1) \
                              - (((value - minimum) \
                                  / float(maximum - minimum)) \
                                 * (distance_scale - 1))) \
                                 + 1

              raster_utils.vectorize_datasets([fdistance_uri],
                                              normalize_op,
                                              normalized_uri,
                                              transition_type,
                                              transition_nodata,
                                              cell_size,
                                              "union")

              proximity_dict[cover_id] = normalized_uri

    def constraint_op(suit, cons):
        return suit * cons

    def proximity_op(suit, prox):
        v = suit + (prox * proximity_weight)
        if v > 100:
            return 100
        else:
            return v

    def constraint_proximity_op(suit, cons, prox):
        v = (cons * suit) + (prox * proximity_weight)
        if v > 100:
            return 100
        else:
            return v
      
    for cover_id in suitability_dict:
        suitability_uri = os.path.join(workspace, adjusted_suitability_name % cover_id)
        if args["calculate_constraints"]:
            if cover_id in proximity_dict:
                LOGGER.info("Combining suitability, proximity, and constraints for %i.", cover_id)
                uri_list = [suitability_dict[cover_id],
                            constraints_ds_uri,
                            proximity_dict[cover_id]]
                LOGGER.info("Vectorizing: %s", ", ".join(uri_list))
                raster_utils.vectorize_datasets(uri_list,
                                                constraint_proximity_op,
                                                suitability_uri,
                                                transition_type,
                                                transition_nodata,
                                                cell_size,
                                                "union")
                suitability_dict[cover_id] = suitability_uri
                
            else:
                LOGGER.info("Combining suitability and constraints for %i.", cover_id)
                uri_list = [suitability_dict[cover_id],
                            constraints_ds_uri]
                LOGGER.info("Vectorizing: %s", ", ".join(uri_list))
                raster_utils.vectorize_datasets(uri_list,
                                                constraint_op,
                                                suitability_uri,
                                                transition_type,
                                                transition_nodata,
                                                cell_size,
                                                 "union")
                suitability_dict[cover_id] = suitability_uri

        elif cover_id in proximity_dict:
            LOGGER.info("Combining suitability and proximity for %i.", cover_id)
            uri_list = [suitability_dict[cover_id],
                        proximity_dict[cover_id]]
            LOGGER.info("Vectorizing: %s", ", ".join(uri_list))
            raster_utils.vectorize_datasets(uri_list,
                                            proximity_op,
                                            suitability_uri,
                                            transition_type,
                                            transition_nodata,
                                            cell_size,
                                            "union")
            suitability_dict[cover_id] = suitability_uri


   
    #normalize probabilities to be on a 10 point scale
    #probability raster (reclass using probability matrix)

    #proximity raster (gaussian for each landcover type, using max distance)
    #InVEST 2 uses 4-connectedness?

    #combine rasters for weighting into sutibility raster, multiply proximity by 0.3
    #[suitability * (1-factor weight)] + (factors * factor weight) or only single raster

    ###
    #reallocate pixels (disk heap sort, randomly reassign equal value pixels, applied in order)
    ###

    #copy initial LULC
    scenario_uri = os.path.join(workspace, scenario_name)            

    src_ds = gdal.Open(landcover_uri)
    n_cols = src_ds.RasterXSize
    n_rows = src_ds.RasterYSize

    dst_ds = driver.CreateCopy(scenario_uri, src_ds, 0)
    dst_ds = None
    src_ds = None
       
    #identify LULC types undergoing change
    change_list = []
    if args["calculate_priorities"]:
       for cover_id in transition_dict:
           percent_change = transition_dict[cover_id][args["percent_field"]]
           area_change = transition_dict[cover_id][args["area_field"]]
           if percent_change > 0:
               change_list.append((priorities_dict[cover_id],
                                   cover_id,
                                   int((percent_change / 100.0) \
                                   * landcover_count_dict[cover_id])))
           elif area_change > 0:
               change_list.append((priorities_dict[cover_id],
                                   cover_id,
                                   int(math.ceil(area_change / cell_size))))
           else:
               LOGGER.warn("Cover %i suitability specified, but no change indicated.", cover_id)
    else:
        for cover_id in transition_dict:
            percent_change = transition_dict[cover_id][args["percent_field"]]
            area_change = transition_dict[cover_id][args["area_field"]]
            if percent_change > 0:
                change_list.append((transition_dict[cover_id][args["priority_field"]],
                                    cover_id,
                                    int((percent_change / 100.0) \
                                    * landcover_count_dict[cover_id])))
            elif area_change > 0:
                change_list.append((transition_dict[cover_id][args["priority_field"]],
                                   cover_id,
                                   int(math.ceil(area_change / cell_size))))
            else:
                LOGGER.warn("Cover %i suitability specified, but no change indicated.", cover_id)
        

    change_list.sort(reverse=True)

    #change pixels
    scenario_ds = gdal.Open(scenario_uri, 1)
    scenario_band = scenario_ds.GetRasterBand(1)

    unconverted_pixels = {}
    for index, (priority, cover_id, count) in enumerate(change_list):
        LOGGER.debug("Increasing cover %i by %i pixels.", cover_id, count)

        #open all lower priority suitability rasters and assign changed pixels value of 0
        update_ds = {}
        update_bands = {}
        for _, update_id, _ in change_list[index+1:]:
           update_ds[update_id] = gdal.Open(suitability_dict[cover_id], 1)
           update_bands[update_id] = update_ds[update_id].GetRasterBand(1)
           
        #select pixels
        pixel_heap = disk_sort.sort_to_disk(suitability_dict[cover_id], cover_id)

        for n, (value, flat_index, dataset_index) in enumerate(pixel_heap):
            if n == count or value == 0:
                if value == 0:
                    LOGGER.debug("Incomplete conversion. Only %i pixels converted for %i.", n, cover_id)
                    unconverted_pixels[cover_id] = count - (n -1)
                break
            scenario_band.WriteArray(numpy.array([[cover_id]]), flat_index % n_cols, flat_index / n_cols)

            for c_id in update_bands:
                update_bands[c_id].WriteArray(numpy.array([[0]]), flat_index % n_cols, flat_index / n_cols)

        for c_id in update_bands:
           update_bands[c_id] = None

        for c_id in update_bands:
            update_bands[c_id] = None

    scenario_band = None
    scenario_ds = None

    #apply override
    if args["override_layer"]:
       LOGGER.info("Overriding pixels using values from field %s.", args["override_field"])
       datasource = ogr.Open(args["override"])
       layer = datasource.GetLayer()
       dataset = gdal.Open(scenario_uri, 1)

       if dataset == None:
           msg = "Could not open landcover transition raster."
           LOGGER.error(msg)
           raise IOError, msg

       if datasource == None:
           msg = "Could not open override vector."
           LOGGER.error(msg)
           raise IOError, msg

       if not bool(args["override_inclusion"]):
           LOGGER.debug("Overriding all touched pixels.")
           options = ["ALL_TOUCHED=TRUE", "ATTRIBUTE=%s" % args["override_field"]]
       else:
           LOGGER.debug("Overriding only pixels with covered center points.")
           options = ["ATTRIBUTE=%s" % args["override_field"]]
       gdal.RasterizeLayer(dataset, [1], layer, options=options)
       dataset.FlushCache()
       datasource = None
       dataset = None

    ###
    #tabulate coverages
    ###

    unique_raster_values_count, transitions = get_transition_set_count_from_uri([landcover_uri, scenario_uri])

    htm = open(landcover_htm_uri,'w')
    htm.write("<HTML><TITLE>Scenario Generator Report</TITLE>")

    htm.write("<B>Initial Landscape</B>")
    htm.write("\n<TABLE BORDER=1>")
    initial_cover_id_list = unique_raster_values_count[landcover_uri].keys()
    initial_cover_id_list.sort()

    htm.write("\n<TR><TD>ID</TD><TD>")
    htm.write("</TD><TD>".join([str(cover_id) for cover_id in initial_cover_id_list]))
    htm.write("\n</TD></TR>")

    htm.write("\n<TR><TD>Count</TD><TD>")
    htm.write("</TD><TD>".join([str(unique_raster_values_count[landcover_uri][cover_id]) for cover_id in initial_cover_id_list]))
    htm.write("\n</TD></TR>")
    
    htm.write("\n</TABLE>")

    htm.write("\n</HTML>")

    htm.write("<P><P><B>Scenario Landscape</B>")
    htm.write("\n<TABLE BORDER=1>")
    scenario_cover_id_list = unique_raster_values_count[scenario_uri].keys()
    scenario_cover_id_list.sort()

    htm.write("\n<TR><TD>ID</TD><TD>")
    htm.write("</TD><TD>".join([str(cover_id) for cover_id in scenario_cover_id_list]))
    htm.write("\n</TD></TR>")

    htm.write("\n<TR><TD>Count</TD><TD>")
    htm.write("</TD><TD>".join([str(unique_raster_values_count[scenario_uri][cover_id]) for cover_id in scenario_cover_id_list]))
    htm.write("\n</TD></TR>")
    
    htm.write("\n</TABLE>")

    cover_dict = {}
    for cover_id in set(unique_raster_values_count[landcover_uri].keys()).union(set(unique_raster_values_count[scenario_uri].keys())):
        try:
            before = unique_raster_values_count[landcover_uri][cover_id]
        except KeyError:
            before = 0
        try:
            after =unique_raster_values_count[scenario_uri][cover_id]
        except KeyError:
            after = 0
        cover_dict[cover_id] = (before, after)

    htm.write("<P><P><B>Change Table</B>")
    htm.write(generate_chart_html(cover_dict))

    htm.write("<P><P><B>Transition Matrix</B>")
    htm.write("\n<TABLE BORDER=1>")    
    htm.write("\n<TR><TD>ID</TD><TD>")
    htm.write("</TD><TD>".join([str(cover_id) for cover_id in scenario_cover_id_list]))
    htm.write("\n</TD></TR>")

    for initial_cover_id in initial_cover_id_list:
        htm.write("\n<TR><TD>%i</TD>" % initial_cover_id)
        for scenario_cover_id in scenario_cover_id_list:
            try:
                htm.write("<TD>%i</TD>" % transitions[0][initial_cover_id][scenario_cover_id])
            except KeyError:
                htm.write("<TD><FONT COLOR=lightgray>%i</FONT></TD>" % 0)

        htm.write("\n</TR>")
       
    htm.write("\n</TABLE>")

    unconverted_cover_id_list = unconverted_pixels.keys()
    unconverted_cover_id_list.sort()
    if len(unconverted_cover_id_list) > 0:
       htm.write("<P><P><B>Unconverted Pixels</B>")
       htm.write("\n<TABLE BORDER=1>")
       htm.write("<TR><TD>ID</TD><TD>Count</TD></TR>")
       for cover_id in unconverted_cover_id_list:
          htm.write("<TR><TD>%i</TD><TD>%i</TD></TR>" % (cover_id, unconverted_pixels[cover_id]))
       htm.write("\n</TABLE>")
    else:
        htm.write("<P><P><I>All target pixels converted.</I>")
    htm.write("\n</HTML>")

    #input CSVs
    input_csv_list = []

    if args["calculate_priorities"]:
       input_csv_list.append((args["priorities_csv_uri"], "Priorities Table"))

    if args["calculate_transition"] or args["calculate_factors"]:
        input_csv_list.append((args["transition"], "Transition Table"))

    if args["calculate_factors"]:
        input_csv_list.append((args["suitability"], "Factors Table"))
    
    htm.write("<P><P><B>Input Tables</B><P><P>")
    for csv_uri, name in input_csv_list:
        table = "\n<TABLE BORDER=1><TR><TD>" + open(csv_uri).read().strip().replace(",","</TD><TD>").replace("\n","</TD></TR><TR><TD>") + "</TD></TR></TABLE>"

        htm.write("<P><P><B>%s</B>" % name)
        htm.write(table)

    htm.close()
