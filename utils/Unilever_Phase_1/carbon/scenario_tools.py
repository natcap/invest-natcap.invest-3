import numpy
import scipy.ndimage
import collections

def expand_lu_type(
    base_array, nodata, expansion_id, converting_id_list, current_step, 
    pixels_per_step, land_cover_start_fractions=None,
    land_cover_end_fractions=None, end_step=None):
    """Given a base array, and a number of pixels to expand
        from, buffer out a conversion of that number of pixels
        
        base_array - a 2D array of integers that represent
            land cover IDs
        nodata - value in base_array to ignore
        expansion_id - the ID type to expand
        converting_id_list - a list of land cover types that the simulation will
            calculate distances from
        expansion_pixel_count - convert this number of pixels
        land_cover_start_percentages/land_cover_end_percentages -
            optional, if defined is a dictionary of list of land cover types
            that are used for conversion during the start step
        end_expansion_pixel_count - defined if land_cover_*_percentages are defined.  use to know what % of total conversion has been reached
        
        returns the new expanded array, the number of pixels per type that were converted to expansion_id
        """
        
    def step_percent(start_fraction, end_fraction):
        total_pixels = 0
        for step_id in range(current_step):
            if end_step != 1:
                current_percent = float(step_id) / (end_step - 1)
            else:
                current_percent = 0.0
            #print current_percent, pixels_per_step
            total_pixels += pixels_per_step * (
                start_fraction * (1-current_percent) + 
                end_fraction * current_percent)
        return total_pixels
            
    expansion_pixel_count = pixels_per_step * current_step
    
    #Calculate the expansion distance
    expansion_existance = base_array != nodata
    for converting_id in converting_id_list:
        expansion_existance = (base_array != converting_id) & expansion_existance
    edge_distance = scipy.ndimage.morphology.distance_transform_edt(
        expansion_existance)
        
    zero_distance_mask = edge_distance == 0
    edge_distance = scipy.ndimage.filters.gaussian_filter(edge_distance, 2.0)
    edge_distance[zero_distance_mask] = numpy.inf
    increasing_distances = numpy.argsort(edge_distance.flat)
    
    result_array = base_array.copy()
    pixels_converted_so_far = 0
    pixel_count = collections.defaultdict(int)
    if land_cover_start_fractions:
        for fraction_index in range(len(land_cover_start_fractions)):
            lu_code_list, lu_start_percent_change = land_cover_start_fractions[fraction_index]
            lu_end_percent_change = land_cover_end_fractions[fraction_index][1]
            lu_edge_distance = edge_distance.copy()
            lu_mask_array = numpy.zeros(shape=edge_distance.shape, dtype=numpy.bool)
            lu_mask_array[:] = False
            for lu_code in lu_code_list:
                lu_mask_array = lu_mask_array | (base_array == lu_code)
            lu_edge_distance[~lu_mask_array] = numpy.inf
            lu_increasing_distances = numpy.argsort(lu_edge_distance.flat)
            lu_pixels_to_convert = int(round(step_percent(lu_start_percent_change, lu_end_percent_change)))
            if lu_pixels_to_convert == 0: continue
            lu_slice_to_convert = result_array.flat[lu_increasing_distances[0:lu_pixels_to_convert]]
            for lu_code in numpy.unique(lu_slice_to_convert):
                pixel_count[lu_code] += int(numpy.count_nonzero(lu_slice_to_convert == lu_code))
            result_array.flat[lu_increasing_distances[0:lu_pixels_to_convert]] = expansion_id
            if lu_edge_distance.flat[lu_increasing_distances[lu_pixels_to_convert-1]] == numpy.inf:
                print lu_edge_distance.flat[lu_increasing_distances]
                print lu_edge_distance
                print lu_edge_distance.flat[lu_increasing_distances[0]]
                print lu_edge_distance.flat[lu_increasing_distances[lu_pixels_to_convert-1]]
                print lu_edge_distance.flat[lu_increasing_distances[lu_pixels_to_convert]]
                raise Exception("We used up all the landcover type %s, stopping composite scenario" % lu_code_list)
            pixels_converted_so_far += int(lu_pixels_to_convert)
            
        edge_distance[result_array == expansion_id] = numpy.inf
        #print expansion_pixel_count - pixels_converted_so_far
    
    remaining_pixels = result_array.flat[increasing_distances[0:(expansion_pixel_count - pixels_converted_so_far)]]
    for lu_code in numpy.unique(remaining_pixels):
        pixel_count[lu_code] += numpy.count_nonzero(remaining_pixels == lu_code)
    result_array.flat[increasing_distances[0:(expansion_pixel_count - pixels_converted_so_far)]] = expansion_id
        
    return result_array, pixel_count
