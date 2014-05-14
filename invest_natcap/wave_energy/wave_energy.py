"""InVEST Wave Energy Model Core Code"""
import math
import os
import logging
import csv
import struct
import itertools

import numpy as np
from osgeo import gdal
import osgeo.osr as osr
from osgeo import ogr
from scipy import stats
from bisect import bisect
import scipy

from invest_natcap.dbfpy import dbf
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
LOGGER = logging.getLogger('wave_energy')

def execute(args):
    """Executes both the biophysical and valuation parts of the
        wave energy model (WEM). Files will be written on disk to the
        intermediate and output directories. The outputs computed for
        biophysical and valuation include: wave energy capacity raster,
        wave power raster, net present value raster, percentile rasters for the
        previous three, and a point shapefile of the wave points with
        attributes.

        args - a pythong dictionary that houses the inputs for the model

        args['workspace_dir'] - Where the intermediate and output folder/files
            will be saved. (required)

        args['wave_base_data_uri'] - Directory location of wave base data
            including WW3 data and analysis area shapefile. (required)

        args['analysis_area_uri'] - A string identifying the analysis area of
            interest. Used to determine wave data shapefile, wave data text
            file, and analysis area boundary shape. (required)

        args['machine_perf_uri'] - The path of a CSV file that holds the
            machine performance table. (required)

        args['machine_param_uri'] - The path of a CSV file that holds the
            machine parameter table. (required)

        args['dem_uri'] - The path of the Global Digital Elevation Model (DEM).
            (required)

        args['aoi_uri'] - A polygon shapefile outlining a more detailed area
            within the analysis area. This shapefile should be projected with
            linear units being in meters. (required to run Valuation model)

        args['land_gridPts_uri'] - A CSV file path containing the Landing and
            Power Grid Connection Points table. (required for Valuation)

        args['machine_econ_uri'] - A CSV file path for the machine economic
            parameters table. (required for Valuation)

        args['number_of_machines'] - An integer specifying the number of
            machines for a wave farm site. (required for Valuation)

        args['suffix'] - A python string of characters to append to each output
            filename (optional)

        returns nothing."""

    # Create the Output and Intermediate directories if they do not exist.
    workspace = args['workspace_dir']
    output_dir = os.path.join(workspace, 'output')
    intermediate_dir = os.path.join(workspace, 'intermediate')
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Append a _ to the suffix if it's not empty and doens't already have one
    try:
        file_suffix = args['suffix']
        if file_suffix != "" and not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''

    # Get the uri for the DEM
    dem_uri = args['dem_uri']

    # Create a dictionary that stores the wave periods and wave heights as
    # arrays. Also store the amount of energy the machine produces
    # in a certain wave period/height state as a 2D array
    machine_perf_dict = {}
    machine_perf_file = open(args['machine_perf_uri'])
    reader = csv.reader(machine_perf_file)
    # Get the column header which is the first row in the file
    # and specifies the range of wave periods
    periods = reader.next()
    machine_perf_dict['periods'] = periods[1:]
    # Set the keys for storing wave height range and the machine performance
    # at each state
    machine_perf_dict['heights'] = []
    machine_perf_dict['bin_matrix'] = []
    for row in reader:
        # Build up the row header by taking the first element in each row
        # This is the range of heights
        machine_perf_dict['heights'].append(row.pop(0))
        machine_perf_dict['bin_matrix'].append(row)
    machine_perf_file.close()
    LOGGER.debug('Machine Performance Rows : %s', machine_perf_dict['periods'])
    LOGGER.debug('Machine Performance Cols : %s', machine_perf_dict['heights'])

    # Create a dictionary whose keys are the 'NAMES' from the machine parameter
    # table and whose values are from the corresponding 'VALUES' field.
    machine_param_dict = {}
    machine_param_file = open(args['machine_param_uri'])
    reader = csv.DictReader(machine_param_file)
    for row in reader:
        row_name = row['NAME'].strip().lower()
        machine_param_dict[row_name] = row['VALUE']
    machine_param_file.close()

    # Build up a dictionary of possible analysis areas where the key
    # is the analysis area selected and the value is a dictionary
    # that stores the related uri paths to the needed inputs
    wave_base_data_uri = args['wave_base_data_uri']
    analysis_dict = {
            'West Coast of North America and Hawaii': {
             'point_shape': os.path.join(
                wave_base_data_uri, 'NAmerica_WestCoast_4m.shp'),
             'extract_shape': os.path.join(
                 wave_base_data_uri, 'WCNA_extract.shp'),
             'ww3_uri': os.path.join(
                 wave_base_data_uri, 'NAmerica_WestCoast_4m.txt.bin')
            },
            'East Coast of North America and Puerto Rico': {
             'point_shape': os.path.join(
                wave_base_data_uri, 'NAmerica_EastCoast_4m.shp'),
             'extract_shape': os.path.join(
                 wave_base_data_uri, 'ECNA_extract.shp'),
             'ww3_uri': os.path.join(
                 wave_base_data_uri, 'NAmerica_EastCoast_4m.txt.bin')
            },
            'North Sea 4 meter resolution': {
             'point_shape': os.path.join(
                wave_base_data_uri, 'North_Sea_4m.shp'),
             'extract_shape': os.path.join(
                 wave_base_data_uri, 'North_Sea_4m_Extract.shp'),
             'ww3_uri': os.path.join(
                 wave_base_data_uri, 'North_Sea_4m.bin')
            },
            'North Sea 10 meter resolution': {
             'point_shape': os.path.join(
                wave_base_data_uri, 'North_Sea_10m.shp'),
             'extract_shape': os.path.join(
                 wave_base_data_uri, 'North_Sea_10m_Extract.shp'),
             'ww3_uri': os.path.join(
                 wave_base_data_uri, 'North_Sea_10m.bin')
            },
            'Australia': {
             'point_shape': os.path.join(
                wave_base_data_uri, 'Australia_4m.shp'),
             'extract_shape': os.path.join(
                 wave_base_data_uri, 'Australia_Extract.shp'),
             'ww3_uri': os.path.join(
                 wave_base_data_uri, 'Australia_4m.bin')
            },
           'Global': {
             'point_shape': os.path.join(wave_base_data_uri, 'Global.shp'),
             'extract_shape': os.path.join(
                 wave_base_data_uri, 'Global_extract.shp'),
             'ww3_uri': os.path.join(
                 wave_base_data_uri, 'Global_WW3.txt.bin')
            }
       }

    # Get the String value for the analysis area provided from the dropdown menu
    # in the user interaface
    analysis_area_uri = args['analysis_area_uri']
    # Use the analysis area String to get the uri's to the wave seastate data,
    # the wave point shapefile, and the polygon extract shapefile
    wave_seastate_bins = load_binary_wave_data(
            analysis_dict[analysis_area_uri]['ww3_uri'])
    analysis_area_points_uri = analysis_dict[analysis_area_uri]['point_shape']
    analysis_area_extract_uri = \
            analysis_dict[analysis_area_uri]['extract_shape']

    # Path for clipped wave point shapefile holding wave attribute information
    clipped_wave_shape_path = os.path.join(
            intermediate_dir, 'WEM_InputOutput_Pts%s.shp' % file_suffix)

    # Intermediate paths for wave energy and wave power rasters
    wave_energy_unclipped_path = os.path.join(
            intermediate_dir, 'capwe_mwh_unclipped%s.tif' % file_suffix)
    wave_power_unclipped_path = os.path.join(
            intermediate_dir, 'wp_kw_unclipped%s.tif' % file_suffix)

    # Final output paths for wave energy and wave power rasters
    wave_energy_path = os.path.join(output_dir, 'capwe_mwh%s.tif' % file_suffix)
    wave_power_path = os.path.join(output_dir, 'wp_kw%s.tif' % file_suffix)

    # Paths for wave energy and wave power percentile rasters
    wp_rc_path = os.path.join(output_dir, 'wp_rc%s.tif' % file_suffix)
    capwe_rc_path = os.path.join(output_dir, 'capwe_rc%s.tif' % file_suffix)

    # Set nodata value and datatype for new rasters
    nodata = float(np.finfo(np.float32).min) + 1.0
    datatype = gdal.GDT_Float32
    # Since the global dem is the finest resolution we get as an input,
    # use its pixel sizes as the sizes for the new rasters. We will need the
    # geotranform to get this information later
    dem_gt = raster_utils.get_geotransform_uri(dem_uri)

    # Set the source projection for a coordinate transformation
    # to the input projection from the wave watch point shapefile
    analysis_area_sr = raster_utils.get_spatial_ref_uri(
            analysis_area_points_uri)

    # This try/except statement differentiates between having an AOI or doing
    # a broad run on all the wave watch points specified by
    # args['analysis_area'].
    if 'aoi_uri' not in args:
        LOGGER.debug('AOI not provided')

        # The uri to a polygon shapefile that specifies the broader area
        # of interest
        aoi_shape_path = analysis_area_extract_uri

        # Make a copy of the wave point shapefile so that the original input is
        # not corrupted
        raster_utils.copy_datasource_uri(
                analysis_area_points_uri, clipped_wave_shape_path)

        # Set the pixel size to that of DEM, to be used for creating rasters
        pixel_size = (float(dem_gt[1]) + np.absolute(float(dem_gt[5]))) / 2.0
        LOGGER.debug('Pixel size in meters : %f', pixel_size)

        # Create a coordinate transformation, because it is used below when
        # indexing the DEM
        aoi_sr = raster_utils.get_spatial_ref_uri(analysis_area_extract_uri)
        coord_trans, coord_trans_opposite = get_coordinate_transformation(
                analysis_area_sr, aoi_sr)
    else:
        LOGGER.debug('AOI was provided')
        aoi_shape_path = args['aoi_uri']

        # Temporary shapefile path needed for an intermediate step when
        # changing the projection
        projected_wave_shape_path = os.path.join(
                intermediate_dir, 'projected_wave_data%s.shp' % file_suffix)

        # Set the wave data shapefile to the same projection as the
        # area of interest
        temp_sr = raster_utils.get_spatial_ref_uri(aoi_shape_path)
        output_wkt = temp_sr.ExportToWkt()
        raster_utils.reproject_datasource_uri(
                analysis_area_points_uri, output_wkt, projected_wave_shape_path)

        # Clip the wave data shape by the bounds provided from the
        # area of interest
        clip_shape(projected_wave_shape_path, aoi_shape_path,
                clipped_wave_shape_path)

        aoi_proj_uri = os.path.join(
                intermediate_dir, 'aoi_proj_to_extract%s.shp' % file_suffix)

        # Get the spacial reference of the Extract shape and export to WKT to
        # use in reprojecting the AOI
        extract_sr = raster_utils.get_spatial_ref_uri(analysis_area_extract_uri)
        extract_wkt = extract_sr.ExportToWkt()

        # Project AOI to Extract shape
        raster_utils.reproject_datasource_uri(
                aoi_shape_path, extract_wkt, aoi_proj_uri)

        aoi_clipped_to_extract_uri = os.path.join(
                intermediate_dir,
                'aoi_clipped_to_extract_uri%s.shp' % file_suffix)

        # Clip the AOI to the Extract shape to make sure the output results do
        # not show extrapolated values outside the bounds of the points
        clip_shape(
                aoi_proj_uri, analysis_area_extract_uri,
                aoi_clipped_to_extract_uri)

        aoi_clip_proj_uri = os.path.join(
                intermediate_dir, 'aoi_clip_proj_uri%s.shp' % file_suffix)

        # Reproject the clipped AOI back
        raster_utils.reproject_datasource_uri(
                aoi_clipped_to_extract_uri, output_wkt, aoi_clip_proj_uri)

        aoi_shape_path = aoi_clip_proj_uri

        # Create a coordinate transformation from the given
        # WWIII point shapefile, to the area of interest's projection
        aoi_sr = raster_utils.get_spatial_ref_uri(aoi_shape_path)
        coord_trans, coord_trans_opposite = get_coordinate_transformation(
                analysis_area_sr, aoi_sr)

        # Get the size of the pixels in meters, to be used for creating
        # projected wave power and wave energy capacity rasters
        pixel_xsize, pixel_ysize = pixel_size_helper(
                clipped_wave_shape_path, coord_trans, coord_trans_opposite,
                dem_uri)

        # Average the pixel sizes incase they are of different sizes
        pixel_size = (abs(pixel_xsize) + abs(pixel_ysize)) / 2.0
        LOGGER.debug('Pixel size in meters : %f', pixel_size)

    # We do all wave power calculations by manipulating the fields in
    # the wave data shapefile, thus we need to add proper depth values
    # from the raster DEM
    LOGGER.debug('Adding a depth field to the shapefile from the DEM raster')

    def index_dem_uri(point_shape_uri, dataset_uri, field_name, coord_trans):
        """Index into a gdal raster and where a point from an ogr datasource
            overlays a pixel, add that pixel value to the point feature

            point_shape_uri - a uri to an ogr point shapefile
            dataset_uri - a uri to a gdal dataset
            field_name - a String for the name of the new field that will be
                added to the point feauture
            coord_trans - a coordinate transformation used to make sure the
                datasource and dataset are in the same units

            returns - Nothing"""
        # NOTE: This function is a wrapper function so that we can handle
        # datasets / datasource by passing URI's. This function lacks memory
        # efficiency and the global dem is being dumped into an array. This may
        # cause the global biophysical run to crash
        tmp_dem_path = raster_utils.temporary_filename()

        clipped_wave_shape = ogr.Open(point_shape_uri, 1)
        dem_gt = raster_utils.get_geotransform_uri(dataset_uri)
        dem_matrix = raster_utils.load_dataset_to_carray(
            dataset_uri, tmp_dem_path, array_type=None)

        # Create a new field for the depth attribute
        field_defn = ogr.FieldDefn(field_name, ogr.OFTReal)

        clipped_wave_layer = clipped_wave_shape.GetLayer()
        clipped_wave_layer.CreateField(field_defn)
        feature = clipped_wave_layer.GetNextFeature()

        # For all the features (points) add the proper depth value from the DEM
        while feature is not None:
            depth_index = feature.GetFieldIndex(field_name)
            geom = feature.GetGeometryRef()
            geom_x, geom_y = geom.GetX(), geom.GetY()

            # Transform two points into meters
            point_decimal_degree = coord_trans.TransformPoint(
                    geom_x, geom_y)

            # To get proper depth value we must index into the dem matrix
            # by getting where the point is located in terms of the matrix
            i = int((point_decimal_degree[0] - dem_gt[0]) / dem_gt[1])
            j = int((point_decimal_degree[1] - dem_gt[3]) / dem_gt[5])
            depth = dem_matrix[j][i]
            # There are cases where the DEM may be to coarse and thus a wave
            # energy point falls on land. If the depth value taken from the DEM
            # is greater than or equal to zero we need to delete that point as
            # it should not be used in calculations
            if depth >= 0.0:
                clipped_wave_layer.DeleteFeature(feature.GetFID())
                feature = clipped_wave_layer.GetNextFeature()
            else:
                feature.SetField(int(depth_index), float(depth))
                clipped_wave_layer.SetFeature(feature)
                feature = None
                feature = clipped_wave_layer.GetNextFeature()
        # It is not enough to just delete a feature from the layer. The database
        # where the information is stored must be re-packed so that feature
        # entry is properly removed
        clipped_wave_shape.ExecuteSQL(
                'REPACK ' + clipped_wave_layer.GetName())

        dem_matrix = None

    # Add the depth value to the wave points by indexing into the DEM dataset
    index_dem_uri(
            clipped_wave_shape_path, dem_uri, 'DEPTH_M', coord_trans_opposite)

    LOGGER.debug('Finished adding depth field to shapefile from DEM raster')

    # Generate an interpolate object for wave_energy_capacity
    LOGGER.debug('Interpolating machine performance table')

    energy_interp = wave_energy_interp(wave_seastate_bins, machine_perf_dict)

    # Create a dictionary with the wave energy capacity sums from each location
    LOGGER.info('Calculating Captured Wave Energy.')
    energy_cap = compute_wave_energy_capacity(
        wave_seastate_bins, energy_interp, machine_param_dict)

    # Add the sum as a field to the shapefile for the corresponding points
    LOGGER.debug('Adding the wave energy sums to the WaveData shapefile')
    captured_wave_energy_to_shape(energy_cap, clipped_wave_shape_path)

    # Calculate wave power for each wave point and add it as a field
    # to the shapefile
    LOGGER.info('Calculating Wave Power.')
    wave_power(clipped_wave_shape_path)

    # Create blank rasters bounded by the shape file of analyis area
    raster_utils.create_raster_from_vector_extents_uri(
            aoi_shape_path, pixel_size, datatype, nodata,
            wave_energy_unclipped_path)

    raster_utils.create_raster_from_vector_extents_uri(
            aoi_shape_path, pixel_size, datatype, nodata,
            wave_power_unclipped_path)

    # Interpolate wave energy and wave power from the shapefile over the rasters
    LOGGER.debug('Interpolate wave power and wave energy capacity onto rasters')

    raster_utils.vectorize_points_uri(
            clipped_wave_shape_path, 'CAPWE_MWHY', wave_energy_unclipped_path)

    raster_utils.vectorize_points_uri(
            clipped_wave_shape_path, 'WE_kWM', wave_power_unclipped_path)

    # Clip the wave energy and wave power rasters so that they are confined
    # to the AOI
    raster_utils.clip_dataset_uri(
            wave_power_unclipped_path, aoi_shape_path, wave_power_path, False)

    raster_utils.clip_dataset_uri(
            wave_energy_unclipped_path, aoi_shape_path, wave_energy_path, False)

    # Create the percentile rasters for wave energy and wave power
    # These values are hard coded in because it's specified explicitly in
    # the user's guide what the percentile ranges are and what the units
    # will be.
    percentiles = [25, 50, 75, 90]
    capwe_units_short = ' (MWh/yr)'
    capwe_units_long = ' megawatt hours per year (MWh/yr)'
    wp_units_short = ' (kW/m)'
    wp_units_long = ' wave power per unit width of wave crest length (kW/m)'
    starting_percentile_range = '1'

    create_percentile_rasters(wave_energy_path, capwe_rc_path,
            capwe_units_short, capwe_units_long, starting_percentile_range,
            percentiles, aoi_shape_path)

    create_percentile_rasters(wave_power_path, wp_rc_path, wp_units_short,
            wp_units_long, starting_percentile_range, percentiles,
            aoi_shape_path)

    LOGGER.info('Completed Wave Energy Biophysical')

    valuation_checked = args.pop('valuation_container', False)
    if not valuation_checked:
        LOGGER.debug('Valuation not selected')
        #The rest of the function is valuation, so we can quit now
        return

    # Output path for landing point shapefile
    land_pt_path = os.path.join(
            output_dir, 'LandPts_prj%s.shp' % file_suffix)
    # Output path for grid point shapefile
    grid_pt_path = os.path.join(
            output_dir, 'GridPts_prj%s.shp' % file_suffix)
    # Output path for the projected net present value raster
    raster_projected_path = os.path.join(
            intermediate_dir, 'npv_not_clipped%s.tif' % file_suffix)
    # Path for the net present value percentile raster
    npv_rc_path = os.path.join(output_dir, 'npv_rc%s.tif' % file_suffix)

    # Read machine economic parameters into a dictionary
    machine_econ = {}
    machine_econ_file = open(args['machine_econ_uri'])
    reader = csv.DictReader(machine_econ_file)
    LOGGER.debug('reader fieldnames : %s ', reader.fieldnames)
    # Read in the field names from the column headers
    name_key = reader.fieldnames[0]
    value_key = reader.fieldnames[1]
    for row in reader:
        # Convert name to lowercase
        name = row[name_key].strip().lower()
        LOGGER.debug('Name : %s and Value : % s', name, row[value_key])
        machine_econ[name] = row[value_key]
    machine_econ_file.close()

    # Read landing and power grid connection points into a dictionary
    land_grid_pts = {}
    land_grid_pts_file = open(args['land_gridPts_uri'])
    reader = csv.DictReader(land_grid_pts_file)
    for row in reader:
        LOGGER.debug('Land Grid Row: %s', row)
        if row['ID'] in land_grid_pts:
            land_grid_pts[row['ID'].strip()][row['TYPE']] = \
                    [row['LAT'], row['LONG']]
        else:
            land_grid_pts[row['ID'].strip()] = {
                    row['TYPE']:[row['LAT'], row['LONG']]}

    LOGGER.debug('New Land_Grid Dict : %s', land_grid_pts)
    land_grid_pts_file.close()

    # Number of machines for a given wave farm
    units = int(args['number_of_machines'])
    # Extract the machine economic parameters
    # machine_econ = args['machine_econ']
    cap_max = float(machine_econ['capmax'])
    capital_cost = float(machine_econ['cc'])
    cml = float(machine_econ['cml'])
    cul = float(machine_econ['cul'])
    col = float(machine_econ['col'])
    omc = float(machine_econ['omc'])
    price = float(machine_econ['p'])
    drate = float(machine_econ['r'])
    smlpm = float(machine_econ['smlpm'])

    # The NPV is for a 25 year period
    year = 25.0

    # A numpy array of length 25, representing the npv of a farm for
    # each year
    time = np.linspace(0.0, year - 1.0, year)

    # The discount rate calculation for the npv equations
    rho = 1.0 / (1.0 + drate)

    # Extract the landing and grid points data
    grid_pts = {}
    land_pts = {}
    for key, value in land_grid_pts.iteritems():
        grid_pts[key] = [value['GRID'][0], value['GRID'][1]]
        land_pts[key] = [value['LAND'][0], value['LAND'][1]]

    # Make a point shapefile for landing points.
    LOGGER.info('Creating Landing Points Shapefile.')
    build_point_shapefile(
            'ESRI Shapefile', 'landpoints', land_pt_path, land_pts,
            aoi_sr, coord_trans)

    # Make a point shapefile for grid points
    LOGGER.info('Creating Grid Points Shapefile.')
    build_point_shapefile(
            'ESRI Shapefile', 'gridpoints', grid_pt_path, grid_pts,
            aoi_sr, coord_trans)

    # Get the coordinates of points of wave_data_shape, landing_shape,
    # and grid_shape
    we_points = get_points_geometries(clipped_wave_shape_path)
    landing_points = get_points_geometries(land_pt_path)
    grid_point = get_points_geometries(grid_pt_path)

    # Calculate the distances between the relative point groups
    LOGGER.info('Calculating Distances.')
    wave_to_land_dist, wave_to_land_id = calculate_distance(
            we_points, landing_points)
    land_to_grid_dist, _ = calculate_distance(
            landing_points,  grid_point)

    def add_distance_fields_uri(
            wave_shape_uri, ocean_to_land_dist, land_to_grid_dist):
        """A wrapper function that adds two fields to the wave point
            shapefile: the distance from ocean to land and the
            distance from land to grid.

            wave_shape_uri - a uri path to the wave points shapefile
            ocean_to_land_dist - a numpy array of distance values
            land_to_grid_dist - a numpy array of distance values

            returns - Nothing"""
        wave_data_shape = ogr.Open(wave_shape_uri, 1)
        wave_data_layer = wave_data_shape.GetLayer(0)
        # Add three new fields to the shapefile that will store
        # the distances
        for field in ['W2L_MDIST', 'LAND_ID', 'L2G_MDIST']:
            field_defn = ogr.FieldDefn(field, ogr.OFTReal)
            wave_data_layer.CreateField(field_defn)
        # For each feature in the shapefile add the corresponding
        # distances from wave_to_land_dist and land_to_grid_dist
        # that was calculated above
        iterate_feat = 0
        wave_data_layer.ResetReading()
        feature = wave_data_layer.GetNextFeature()
        while feature is not None:
            ocean_to_land_index = feature.GetFieldIndex('W2L_MDIST')
            land_to_grid_index = feature.GetFieldIndex('L2G_MDIST')
            id_index = feature.GetFieldIndex('LAND_ID')

            land_id = int(wave_to_land_id[iterate_feat])

            feature.SetField(
                    ocean_to_land_index,
                    ocean_to_land_dist[iterate_feat])
            feature.SetField(
                    land_to_grid_index, land_to_grid_dist[land_id])
            feature.SetField(id_index, land_id)

            iterate_feat = iterate_feat + 1

            wave_data_layer.SetFeature(feature)
            feature = None
            feature = wave_data_layer.GetNextFeature()

    add_distance_fields_uri(
            clipped_wave_shape_path, wave_to_land_dist,
            land_to_grid_dist)

    def npv_wave(annual_revenue, annual_cost):
        """Calculates the NPV for a wave farm site based on the
            annual revenue and annual cost

            annual_revenue - A numpy array of the annual revenue for
                the first 25 years
            annual_cost - A numpy array of the annual cost for the
                first 25 years

            returns - The Total NPV which is the sum of all 25 years
        """
        npv = []
        for i in range(len(time)):
            npv.append(rho ** i * (annual_revenue[i] - annual_cost[i]))
        return sum(npv)

    def compute_npv_farm_energy_uri(wave_points_uri):
        """A wrapper function for passing uri's to compute the
            Net Present Value. Also computes the total captured
            wave energy for the entire farm.

            wave_points_uri - a uri path to the wave energy points

            returns - Nothing"""

        wave_points = ogr.Open(wave_points_uri, 1)
        wave_data_layer = wave_points.GetLayer()
        # Add Net Present Value field, Total Captured Wave Energy field,
        # and Units field to shapefile
        for field_name in ['NPV_25Y', 'CAPWE_ALL', 'UNITS']:
            field_defn = ogr.FieldDefn(field_name, ogr.OFTReal)
            wave_data_layer.CreateField(field_defn)
        wave_data_layer.ResetReading()
        feat_npv = wave_data_layer.GetNextFeature()
        # For all the wave farm sites, calculate npv and write to
        # shapefile
        LOGGER.info('Calculating the Net Present Value.')
        while feat_npv is not None:
            depth_index = feat_npv.GetFieldIndex('DEPTH_M')
            wave_to_land_index = feat_npv.GetFieldIndex('W2L_MDIST')
            land_to_grid_index = feat_npv.GetFieldIndex('L2G_MDIST')
            captured_wave_energy_index = feat_npv.GetFieldIndex(
                    'CAPWE_MWHY')
            npv_index = feat_npv.GetFieldIndex('NPV_25Y')
            capwe_all_index = feat_npv.GetFieldIndex('CAPWE_ALL')
            units_index = feat_npv.GetFieldIndex('UNITS')

            depth = feat_npv.GetFieldAsDouble(depth_index)
            wave_to_land = feat_npv.GetFieldAsDouble(wave_to_land_index)
            land_to_grid = feat_npv.GetFieldAsDouble(land_to_grid_index)
            captured_wave_energy = feat_npv.GetFieldAsDouble(
                    captured_wave_energy_index)
            capwe_all_result = captured_wave_energy * units
            # Create a numpy array of length 25, filled with the
            # captured wave energy in kW/h. Represents the
            # lifetime of this wave farm.
            captured_we = np.ones(len(time)) * (
                    int(captured_wave_energy) * 1000.0)
            # It is expected that there is no revenue from the
            # first year
            captured_we[0] = 0
            # Compute values to determine NPV
            lenml = 3.0 * np.absolute(depth)
            install_cost = units * cap_max * capital_cost
            mooring_cost = smlpm * lenml * cml * units
            trans_cost = (wave_to_land * cul / 1000.0) + (
                    land_to_grid * col / 1000.0)
            initial_cost = install_cost + mooring_cost + trans_cost
            annual_revenue = price * units * captured_we
            annual_cost = omc * captured_we * units
            # The first year's costs are the initial start up costs
            annual_cost[0] = initial_cost

            npv_result = npv_wave(annual_revenue, annual_cost) / 1000.0
            feat_npv.SetField(npv_index, npv_result)
            feat_npv.SetField(capwe_all_index, capwe_all_result)
            feat_npv.SetField(units_index, units)

            wave_data_layer.SetFeature(feat_npv)
            feat_npv = None
            feat_npv = wave_data_layer.GetNextFeature()

    compute_npv_farm_energy_uri(clipped_wave_shape_path)

    # Create a blank raster from the extents of the wave farm shapefile
    LOGGER.debug('Creating Raster From Vector Extents')
    raster_utils.create_raster_from_vector_extents_uri(
            clipped_wave_shape_path, pixel_size, datatype, nodata,
            raster_projected_path)
    LOGGER.debug('Completed Creating Raster From Vector Extents')

    # Interpolate the NPV values based on the dimensions and
    # corresponding points of the raster, then write the interpolated
    # values to the raster
    LOGGER.info('Generating Net Present Value Raster.')

    raster_utils.vectorize_points_uri(
            clipped_wave_shape_path, 'NPV_25Y', raster_projected_path)

    npv_out_uri = os.path.join(
            output_dir, 'npv_usd%s.tif' % file_suffix)

    # Clip the raster to the convex hull polygon
    raster_utils.clip_dataset_uri(
            raster_projected_path, aoi_shape_path, npv_out_uri, False)

    #Create the percentile raster for net present value
    percentiles = [25, 50, 75, 90]

    create_percentile_rasters(npv_out_uri, npv_rc_path, ' (US$)',
            ' thousands of US dollars (US$)', '1', percentiles,
            aoi_shape_path)

    LOGGER.debug('End of wave_energy_core.valuation')

def build_point_shapefile(
        driver_name, layer_name, path, data, prj, coord_trans):
    """This function creates and saves a point geometry shapefile to disk.
        It specifically only creates one 'Id' field and creates as many features
        as specified in 'data'

        driver_name - A string specifying a valid ogr driver type
        layer_name - A string representing the name of the layer
        path - A string of the output path of the file
        data - A dictionary who's keys are the Id's for the field
            and who's values are arrays with two elements being
            latitude and longitude
        prj - A spatial reference acting as the projection/datum
        coord_trans - A coordinate transformation

        returns - Nothing """
    #If the shapefile exists, remove it.
    if os.path.isfile(path):
        os.remove(path)
    #Make a point shapefile for landing points.
    driver = ogr.GetDriverByName(driver_name)
    data_source = driver.CreateDataSource(path)
    layer = data_source.CreateLayer(layer_name, prj, ogr.wkbPoint)
    field_defn = ogr.FieldDefn('Id', ogr.OFTInteger)
    layer.CreateField(field_defn)
    #For all of the landing points create a point feature on the layer
    for key, value in data.iteritems():
        latitude = value[0]
        longitude = value[1]
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint_2D(float(longitude), float(latitude))
        geom.Transform(coord_trans)
        #Create the feature, setting the id field to the corresponding id
        #field from the csv file
        feat = ogr.Feature(layer.GetLayerDefn())
        layer.CreateFeature(feat)
        index = feat.GetFieldIndex('Id')
        feat.SetField(index, key)
        feat.SetGeometryDirectly(geom)
        #Save the feature modifications to the layer.
        layer.SetFeature(feat)
        feat = None

def get_points_geometries(shape_uri):
    """This function takes a shapefile and for each feature retrieves
        the X and Y value from it's geometry. The X and Y value are stored in
        a numpy array as a point [x_location,y_location], which is returned
        when all the features have been iterated through.

        shape_uri - An uri to an OGR shapefile datasource

        returns - A numpy array of points, which represent the shape's feature's
              geometries.
    """
    point = []
    shape = ogr.Open(shape_uri)
    layer = shape.GetLayer(0)
    feat = layer.GetNextFeature()
    while feat is not None:
        x_location = float(feat.GetGeometryRef().GetX())
        y_location = float(feat.GetGeometryRef().GetY())
        point.append([x_location, y_location])
        feat = None
        feat = layer.GetNextFeature()

    return np.array(point)

def calculate_distance(xy_1, xy_2):
    """For all points in xy_1, this function calculates the distance
        from point xy_1 to various points in xy_2,
        and stores the shortest distances found in a list min_dist.
        The function also stores the index from which ever point in xy_2
        was closest, as an id in a list that corresponds to min_dist.

        xy_1 - A numpy array of points in the form [x,y]
        xy_2 - A numpy array of points in the form [x,y]

        returns - A numpy array of shortest distances and a numpy array
              of id's corresponding to the array of shortest distances
    """
    #Create two numpy array of zeros with length set to as many points in xy_1
    min_dist = np.zeros(len(xy_1))
    min_id = np.zeros(len(xy_1))
    #For all points xy_point in xy_1 calcuate the distance from xy_point to xy_2
    #and save the shortest distance found.
    for index, xy_point in enumerate(xy_1):
        dists = np.sqrt(np.sum((xy_point - xy_2) ** 2, axis=1))
        min_dist[index], min_id[index] = dists.min(), dists.argmin()
    return min_dist, min_id

def load_binary_wave_data(wave_file_uri):
    """The load_binary_wave_data function converts a pickled WW3 text file
        into a dictionary who's keys are the corresponding (I,J) values
        and whose value is a two-dimensional array representing a matrix
        of the number of hours a seastate occurs over a 5 year period.
        The row and column headers are extracted once and stored in the
        dictionary as well.

        wave_file_uri - The path to a pickled binary WW3 file.

        returns - A dictionary of matrices representing hours of specific seastates,
              as well as the period and height ranges.  It has the following
              structure:
               {'periods': [1,2,3,4,...],
                'heights': [.5,1.0,1.5,...],
                'bin_matrix': { (i0,j0): [[2,5,3,2,...], [6,3,4,1,...],...],
                                (i1,j1): [[2,5,3,2,...], [6,3,4,1,...],...],
                                 ...
                                (in, jn): [[2,5,3,2,...], [6,3,4,1,...],...]
                              }
               }
    """
    LOGGER.debug('Extrapolating wave data from text to a dictionary')
    wave_file = open(wave_file_uri, 'rb')
    wave_dict = {}
    # Create a key that hosts another dictionary where the matrix representation
    # of the seastate bins will be saved
    wave_dict['bin_matrix'] = {}
    wave_array = None
    wave_periods = []
    wave_heights = []
    key = None

    # get rows,cols
    row_col_bin = wave_file.read(8)
    n_cols, n_rows = struct.unpack('ii', row_col_bin)

    # get the periods and heights
    line = wave_file.read(n_cols * 4)

    wave_periods = list(struct.unpack('f' * n_cols, line))
    line = wave_file.read(n_rows * 4)
    wave_heights = list(struct.unpack('f' * n_rows, line))

    key = None
    while True:
        line = wave_file.read(8)
        if len(line) == 0:
            # end of file
            wave_dict['bin_matrix'][key] = np.array(wave_array)
            break

        if key != None:
            wave_dict['bin_matrix'][key] = np.array(wave_array)

        # Clear out array
        wave_array = []

        key = struct.unpack('ii', line)

        for _ in itertools.repeat(None, n_rows):
            line = wave_file.read(n_cols * 4)
            array = list(struct.unpack('f' * n_cols, line))
            wave_array.append(array)

    wave_file.close()
    # Add row/col header to dictionary
    LOGGER.debug('WaveData col %s', wave_periods)
    wave_dict['periods'] = np.array(wave_periods, dtype='f')
    LOGGER.debug('WaveData row %s', wave_heights)
    wave_dict['heights'] = np.array(wave_heights, dtype='f')
    LOGGER.debug('Finished extrapolating wave data to dictionary')
    return wave_dict


def pixel_size_helper(shape_path, coord_trans, coord_trans_opposite, ds_uri):
    """This function helps retrieve the pixel sizes of the global DEM
        when given an area of interest that has a certain projection.

        shape_path - A uri to a point shapefile datasource indicating where
            in the world we are interested in
        coord_trans - A coordinate transformation
        coord_trans_opposite - A coordinate transformation that transforms in the
                           opposite direction of 'coord_trans'
        ds_uri - A uri to a gdal dataset to get the pixel size from

        returns - A tuple of the x and y pixel sizes of the global DEM
              given in the units of what 'shape' is projected in"""
    shape = ogr.Open(shape_path)
    global_dem = gdal.Open(ds_uri)

    # Get a point in the clipped shape to determine output grid size
    feat = shape.GetLayer(0).GetNextFeature()
    geom = feat.GetGeometryRef()
    reference_point_x = geom.GetX()
    reference_point_y = geom.GetY()

    # Convert the point from meters to geom_x/long
    reference_point_latlng = coord_trans_opposite.TransformPoint(
            reference_point_x, reference_point_y)

    # Get the size of the pixels in meters, to be used for creating rasters
    pixel_size_tuple = raster_utils.pixel_size_based_on_coordinate_transform(
            global_dem, coord_trans, reference_point_latlng)

    return pixel_size_tuple


def get_coordinate_transformation(source_sr, target_sr):
    """This function takes a source and target spatial reference and creates
        a coordinate transformation from source to target, and one from target
        to source.

        source_sr - A spatial reference
        target_sr - A spatial reference

        return - A tuple, coord_trans (source to target) and coord_trans_opposite
             (target to source)
    """
    coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
    coord_trans_opposite = osr.CoordinateTransformation(target_sr, source_sr)
    return (coord_trans, coord_trans_opposite)

def create_percentile_rasters(
        raster_path, output_path, units_short, units_long, start_value,
        percentile_list, aoi_shape_path):
    """Creates a percentile (quartile) raster based on the raster_dataset. An
        attribute table is also constructed for the raster_dataset that
        displays the ranges provided by taking the quartile of values.
        The following inputs are required:

        raster_path - A uri to a gdal raster dataset with data of type integer
        output_path - A String for the destination of new raster
        units_short - A String that represents the shorthand for the units
            of the raster values (ex: kW/m)
        units_long - A String that represents the description of the units
            of the raster values (ex: wave power per unit width of
            wave crest length (kW/m))
        start_value - A String representing the first value that goes to the
            first percentile range (start_value - percentile_one)
        percentile_list - a python list of the percentiles ranges
            ex: [25, 50, 75, 90]
        aoi_shape_path - a uri to an OGR polygon shapefile to clip the
            rasters to

        return - Nothing """

    LOGGER.debug('Create Perctile Rasters')

    # If the output_path is already a file, delete it
    if os.path.isfile(output_path):
        os.remove(output_path)

    def raster_percentile(band):
        """Operation to use in vectorize_datasets that takes
            the pixels of 'band' and groups them together based on
            their percentile ranges.

            band - A gdal raster band

            returns - An integer that places each pixel into a group
        """
        return bisect(percentiles, band)
    # Create a memory mapped matrix for the dataset that we're getting the
    # percentiles for
    tmp_matrix_file = raster_utils.temporary_filename()
    matrix = raster_utils.load_memory_mapped_array(
            raster_path, tmp_matrix_file, array_type=None)

    # Get the shape of the matrix to create future memory mapped arrays from
    n_rows, n_cols = matrix.shape

    # Create two more memory mapped arrays for storing operations done on the
    # original matrix. This helps avoid memory errors.
    tmp_mask_file = raster_utils.temporary_filename()
    matrix_mask = np.memmap(
        tmp_mask_file, dtype=bool, mode='w+', shape=(n_rows, n_cols))

    # Flatten each array before doing operations so that it can be passed to
    # scipy.scoreatpercentiles later
    dataset_array = np.reshape(matrix, (-1,))
    dataset_nodata_flat = np.reshape(matrix_mask, (-1))

    # Create a very large negative number to replace the nodata values, so that
    # they are not used when computing the percentiles later
    neg_float = float(np.finfo(np.float32).min) + 1.0
    ds_nodata = raster_utils.get_nodata_from_uri(raster_path)

    # Create a mask of where the nodata values are
    np.equal(dataset_array, ds_nodata, dataset_nodata_flat)

    # Using the above mask, replace the nodata values with a very large negative
    # number
    dataset_array[dataset_nodata_flat] = neg_float
    # Create a masked array based on the array with the redefined nodata values
    # and the nodata mask. This will be helpful when getting the proper min /
    # max value of the array which will be used later.
    dataset_mask = np.ma.masked_array(dataset_array, mask=dataset_nodata_flat)

    # Get the min / max value of the masked array. The masked out values are
    # ignored when getting the min / max so we don't have to worry about the
    # very large negative number. This min / max will be used later in scoring
    # the percentiles
    min_val = dataset_mask.min()
    max_val = dataset_mask.max()
    LOGGER.debug('MIN:MAX : %s:%s', min_val, max_val)

    # Get the percentiles based on the data and percentile ranges we are looking
    # for
    percentiles = get_percentiles(
            dataset_array, percentile_list, min_val, max_val)

    LOGGER.debug('percentiles_list : %s', percentiles)

    # Get the percentile ranges as strings so that they can be added to a output
    # table
    percentile_ranges = create_percentile_ranges(
            percentiles, units_short, units_long, start_value)

    # Add the start_value to the beginning of the percentiles so that any value
    # before the start value is set to nodata
    percentiles.insert(0, int(start_value))

    # Set nodata to a very small negative number
    nodata = np.iinfo(np.int32).min

    pixel_size = raster_utils.get_cell_size_from_uri(raster_path)

    # Classify the pixels of raster_dataset into groups and write
    # then to output
    raster_utils.vectorize_datasets(
            [raster_path], raster_percentile, output_path, gdal.GDT_Int32,
            nodata, pixel_size, 'intersection',
            assert_datasets_projected=False, aoi_uri=aoi_shape_path)

    # Create a memory mapped array for the output percentile raster. This will
    # be used to get the pixel count for each percentile
    tmp_perc_file = raster_utils.temporary_filename()
    perc_array = raster_utils.load_memory_mapped_array(
            output_path, tmp_perc_file, array_type=None)

    # Get the shape of the array so that future memory mapped arrays can be
    # based on it
    count_rows, count_cols = perc_array.shape

    # Initialize a list that will hold pixel counts for each group
    pixel_count = np.zeros(len(percentile_list) + 1)

    percentile_groups = np.arange(1, len(percentiles) + 1)

    LOGGER.debug('Percentile Groups : %s', percentile_groups)
    for percentile_class in percentile_groups:
        # This line of code takes the numpy array 'perc_array', which holds
        # the values from the percentile_band after being grouped, and checks
        # to see where the values are equal to a certain group.
        # This check gives an array of indices where the case was true,
        # so we take the size of that array to give us the number of pixels
        # that fall in that group.

        tmp_count_file = raster_utils.temporary_filename()
        count_mask = np.memmap(
            tmp_count_file, dtype = np.int32, mode = 'w+',
            shape = (count_rows, count_cols))

        np.equal(perc_array, percentile_class, count_mask)
        pixel_count[percentile_class - 1] = np.count_nonzero(count_mask)

    LOGGER.debug('number of pixels per group: : %s', pixel_count)

    # Generate the attribute table for the percentile raster
    create_attribute_table(output_path, percentile_ranges, pixel_count)

def get_percentiles(value_list, percentile_list, min_val, max_val):
    """Creates a list of integers of the percentile marks

        value_list - A list of numbers
        percentile_list - A list of ascending integers of the desired
            percentiles
        min_val - a int/float indicating the lower limit for computing the
            percentile. Values lower will be ignored
        max_val - a int/float indicating the upper limit for computing the
            percentile. Values greater will be ignored

        returns - A list of integers which are the percentile marks"""

    pct_list = []
    for percentile in percentile_list:
        pct_list.append(int(stats.scoreatpercentile(
            value_list, percentile, (min_val, max_val))))
    return pct_list

def create_percentile_ranges(percentiles, units_short, units_long, start_value):
    """Constructs the percentile ranges as Strings, with the first
        range starting at 1 and the last range being greater than the last
        percentile mark.  Each string range is stored in a list that gets returned

        percentiles - A list of the percentile marks in ascending order
        units_short - A String that represents the shorthand for the units of
            the raster values (ex: kW/m)
        units_long - A String that represents the description of the units of
            the raster values (ex: wave power per unit width of
            wave crest length (kW/m))
        start_value - A String representing the first value that goes to the
                 first percentile range (start_value - percentile_one)

        returns - A list of Strings representing the ranges of the percentiles
        """
    length = len(percentiles)
    range_values = []
    # Add the first range with the starting value and long description of units
    # This function will fail and cause an error if the percentile list is empty
    range_first = start_value + ' - ' + str(percentiles[0]) + units_long
    range_values.append(range_first)
    for index in range(length - 1):
        range_values.append(str(percentiles[index]) + ' - ' +
                            str(percentiles[index + 1]) + units_short)
    # Add the last range to the range of values list
    range_last = 'Greater than ' + str(percentiles[length - 1]) + units_short
    range_values.append(range_last)
    LOGGER.debug('range_values : %s', range_values)
    return range_values

def create_attribute_table(raster_uri, percentile_ranges, counter):
    """Creates an attribute table of type '.vat.dbf'.  The attribute table
        created is tied to the dataset of the raster_uri provided as input.
        The table has 3 fields (VALUE, COUNT, VAL_RANGE) where VALUE acts as
        an ID, COUNT is the number of pixels, and VAL_RANGE is the corresponding
        percentile range

        raster_uri - A String of the raster file the table should be associated with
        percentile_ranges - A list of Strings representing the percentile ranges
        counter - A list of integers that represent the pixel count

        returns - nothing"""

    # Create a new dbf file with the same name as the GTiff plus a .vat.dbf
    output_path = raster_uri + '.vat.dbf'
    # If the dbf file already exists, delete it
    if os.path.isfile(output_path):
        os.remove(output_path)
    # Create new table, making readOnly explicit
    dataset_attribute_table = dbf.Dbf(output_path, new = True, readOnly = False)
    # Set the defined fields for the table
    dataset_attribute_table.addField(
                 # integer field
                 ("VALUE", "N", 9),
                 # integer field
                 ("COUNT", "N", 9),
                 # character field, I think header names need to be short?
                 ("VAL_RANGE", "C", 254))
    # Add all the records
    for id_value in range(len(percentile_ranges)):
        LOGGER.debug('id_value: %s', id_value)
        rec = dataset_attribute_table.newRecord()
        rec["VALUE"] = id_value + 1
        rec["COUNT"] = int(counter[id_value])
        rec["VAL_RANGE"] = percentile_ranges[id_value]
        rec.store()
    dataset_attribute_table.close()

def wave_power(shape_uri):
    """Calculates the wave power from the fields in the shapefile
        and writes the wave power value to a field for the corresponding
        feature.

        shape_uri - A uri to a Shapefile that has all the attributes
            represented in fields to calculate wave power at a specific
            wave farm

        returns - Nothing"""
    shape = ogr.Open(shape_uri, 1)

    # Sea water density constant (kg/m^3)
    swd = 1028
    # Gravitational acceleration (m/s^2)
    grav = 9.8
    # Constant determining the shape of a wave spectrum (see users guide pg 23)
    alfa = 0.86
    # Add a waver power field to the shapefile.
    layer = shape.GetLayer()
    field_defn = ogr.FieldDefn('WE_kWM', ogr.OFTReal)
    layer.CreateField(field_defn)
    layer.ResetReading()
    feat = layer.GetNextFeature()
    # For every feature (point) calculate the wave power and add the value
    # to itself in a new field
    while feat is not None:
        height_index = feat.GetFieldIndex('HSAVG_M')
        period_index = feat.GetFieldIndex('TPAVG_S')
        depth_index = feat.GetFieldIndex('DEPTH_M')
        wp_index = feat.GetFieldIndex('WE_kWM')
        height = feat.GetFieldAsDouble(height_index)
        period = feat.GetFieldAsDouble(period_index)
        depth = feat.GetFieldAsInteger(depth_index)

        depth = np.absolute(depth)
        # wave frequency calculation (used to calculate wave number k)
        tem = (2.0 * math.pi) / (period * alfa)
        # wave number calculation (expressed as a function of
        # wave frequency and water depth)
        k = np.square(tem) / (grav * np.sqrt(np.tanh((np.square(tem)) *
                                                     (depth / grav))))
        # Setting numpy overlow error to ignore because when np.sinh
        # gets a really large number it pushes a warning, but Rich
        # and Doug have agreed it's nothing we need to worry about.
        np.seterr(over='ignore')

        # wave group velocity calculation (expressed as a
        # function of wave energy period and water depth)
        wave_group_velocity = (
            ((1 + ((2 * k * depth) / np.sinh(2 * k * depth))) *
             np.sqrt((grav / k) * np.tanh(k * depth))) / 2)

        # Reset the overflow error to print future warnings
        np.seterr(over='print')

        # wave power calculation
        wave_pow = ((((swd * grav) / 16) * (np.square(height)) *
                    wave_group_velocity) / 1000)

        feat.SetField(wp_index, wave_pow)
        layer.SetFeature(feat)
        feat = layer.GetNextFeature()

def clip_shape(shape_to_clip_uri, binding_shape_uri, output_path):
    """Copies a polygon or point geometry shapefile, only keeping the features
        that intersect or are within a binding polygon shape.

        shape_to_clip_uri - A uri to a point or polygon shapefile to clip
        binding_shape_uri - A uri to a polygon shapefile indicating the
            bounds for the shape_to_clip features
        output_path  - The path for the clipped output shapefile

        returns - Nothing"""
    shape_to_clip = ogr.Open(shape_to_clip_uri)
    binding_shape = ogr.Open(binding_shape_uri)

    shape_source = output_path
    # If the output_path is already a file, remove it
    if os.path.isfile(shape_source):
        os.remove(shape_source)
    # Get the layer of points from the current point geometry shape
    in_layer = shape_to_clip.GetLayer(0)
    # Get the layer definition which holds needed attribute values
    in_defn = in_layer.GetLayerDefn()
    # Get the layer of the polygon (binding) geometry shape
    clip_layer = binding_shape.GetLayer(0)
    # Create a new shapefile with similar properties of the
    # current point geometry shape
    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = shp_driver.CreateDataSource(shape_source)
    shp_layer = shp_ds.CreateLayer(in_defn.GetName(), in_layer.GetSpatialRef(),
                                   in_defn.GetGeomType())
    # Get the number of fields in the current point shapefile
    in_field_count = in_defn.GetFieldCount()
    # For every field, create a duplicate field and add it to the
    # new shapefiles layer
    for fld_index in range(in_field_count):
        src_fd = in_defn.GetFieldDefn(fld_index)
        fd_def = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd_def.SetWidth(src_fd.GetWidth())
        fd_def.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd_def)
    LOGGER.debug('Binding Shapes Feature Count : %s',
                 clip_layer.GetFeatureCount())
    LOGGER.debug('Shape to be Bounds Feature Count : %s',
                 in_layer.GetFeatureCount())
    # Retrieve all the binding polygon features and save their cloned
    # geometry references to a list
    clip_feat = clip_layer.GetNextFeature()
    clip_geom_list = []
    while clip_feat is not None:
        clip_geom = clip_feat.GetGeometryRef()
        # Get the spatial reference of the geometry to use in transforming
        source_sr = clip_geom.GetSpatialReference()
        # Retrieve the current point shapes feature and get it's
        # geometry reference
        in_layer.ResetReading()
        in_feat = in_layer.GetNextFeature()
        geom = in_feat.GetGeometryRef()
        # Get the spatial reference of the geometry to use in transforming
        target_sr = geom.GetSpatialReference()
        geom = None
        in_feat = None
        # Create a coordinate transformation
        coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
        # Transform the polygon geometry into the same format as the
        # point shape geometry
        clip_geom.Transform(coord_trans)
        # Add geometry to list
        clip_geom_list.append(clip_geom.Clone())
        clip_feat = clip_layer.GetNextFeature()

    in_layer.ResetReading()
    in_feat = in_layer.GetNextFeature()
    # For all the features in the current point shape (for all the points)
    # Check to see if they Intersect with any of the binding polygons geometry
    # and if they do, copy that point and it's fields to the new shape
    while in_feat is not None:
        # Check to see if the point falls in any of the polygons
        for clip_geom in clip_geom_list:
            geom = in_feat.GetGeometryRef()
            # Intersection returns a new geometry if they intersect, null
            # otherwise.
            geom = geom.Intersection(clip_geom)
            if(geom.GetGeometryCount() + geom.GetPointCount()) != 0:
                # Create a new feature from the input feature and set
                # its geometry
                out_feat = ogr.Feature(feature_def=shp_layer.GetLayerDefn())
                out_feat.SetFrom(in_feat)
                out_feat.SetGeometryDirectly(geom)
                # For all the fields in the feature set the field values from
                # the source field
                for fld_index2 in range(out_feat.GetFieldCount()):
                    src_field = in_feat.GetField(fld_index2)
                    out_feat.SetField(fld_index2, src_field)

                shp_layer.CreateFeature(out_feat)
                out_feat = None
                break

        in_feat = in_layer.GetNextFeature()

def wave_energy_interp(wave_data, machine_perf):
    """Generates a matrix representing the interpolation of the
        machine performance table using new ranges from wave watch data.

        wave_data - A dictionary holding the new x range (period) and
            y range (height) values for the interpolation.  The
            dictionary has the following structure:
              {'periods': [1,2,3,4,...],
               'heights': [.5,1.0,1.5,...],
               'bin_matrix': { (i0,j0): [[2,5,3,2,...], [6,3,4,1,...],...],
                               (i1,j1): [[2,5,3,2,...], [6,3,4,1,...],...],
                                ...
                               (in, jn): [[2,5,3,2,...], [6,3,4,1,...],...]
                             }
              }
        machine_perf - a dictionary that holds the machine performance
            information with the following keys and structure:
                machine_perf['periods'] - [1,2,3,...]
                machine_perf['heights'] - [.5,1,1.5,...]
                machine_perf['bin_matrix'] - [[1,2,3,...],[5,6,7,...],...].

    returns - The interpolated matrix
    """
    # Get ranges and matrix for machine performance table
    x_range = np.array(machine_perf['periods'], dtype='f')
    y_range = np.array(machine_perf['heights'], dtype='f')
    z_matrix = np.array(machine_perf['bin_matrix'], dtype='f')
    # Get new ranges to interpolate to, from wave_data table
    new_x = wave_data['periods']
    new_y = wave_data['heights']

    # Interpolate machine performance table and return the interpolated matrix
    interp_z_spl = scipy.interpolate.RectBivariateSpline(
        x_range, y_range, z_matrix.transpose(), kx=1, ky=1)
    return interp_z_spl(new_x, new_y).transpose()


def compute_wave_energy_capacity(wave_data, interp_z, machine_param):
    """Computes the wave energy capacity for each point and
        generates a dictionary whos keys are the points (I,J) and whos value
        is the wave energy capacity.

        wave_data - A dictionary containing wave watch data with the following
                    structure:
               {'periods': [1,2,3,4,...],
                'heights': [.5,1.0,1.5,...],
                'bin_matrix': { (i0,j0): [[2,5,3,2,...], [6,3,4,1,...],...],
                                (i1,j1): [[2,5,3,2,...], [6,3,4,1,...],...],
                                 ...
                                (in, jn): [[2,5,3,2,...], [6,3,4,1,...],...]
                              }
               }
        interp_z - A 2D array of the interpolated values for the machine
            performance table
        machine_param - A dictionary containing the restrictions for the
            machines (CapMax, TpMax, HsMax)

    returns - A dictionary representing the wave energy capacity at
              each wave point"""

    energy_cap = {}

    # Get the row,col headers (ranges) for the wave watch data
    # row is wave period label
    # col is wave height label
    wave_periods = wave_data['periods']
    wave_heights = wave_data['heights']

    # Get the machine parameter restriction values
    cap_max = float(machine_param['capmax'])
    period_max = float(machine_param['tpmax'])
    height_max = float(machine_param['hsmax'])

    # It seems that the capacity max is already set to it's limit in
    # the machine performance table. However, if it needed to be
    # restricted the following line will do it
    interp_z = np.array(interp_z)
    interp_z[interp_z > cap_max] = cap_max

    # Set position variables to use as a check and as an end
    # point for rows/cols if restrictions limit the ranges
    period_max_index = -1
    height_max_index = -1

    # Using the restrictions find the max position (index) for period and height
    # in the wave_periods/wave_heights ranges

    for index_pos, value in enumerate(wave_periods):
        if (value > period_max):
            period_max_index = index_pos
            break

    for index_pos, value in enumerate(wave_heights):
        if (value > height_max):
            height_max_index = index_pos
            break

    LOGGER.debug('Position of max period : %f', period_max_index)
    LOGGER.debug('Position of max height : %f', height_max_index)

    # For all the wave watch points, multiply the occurence matrix by the
    # interpolated machine performance matrix to get the captured wave energy
    for key, val in wave_data['bin_matrix'].iteritems():
        # Convert all values to type float
        temp_matrix = np.array(val, dtype='f')
        mult_matrix = np.multiply(temp_matrix, interp_z)
        # Set any value that is outside the restricting ranges provided by
        # machine parameters to zero
        if period_max_index != -1:
            mult_matrix[:, period_max_index:] = 0
        if height_max_index != -1:
            mult_matrix[height_max_index:, :] = 0

        # Since we are doing a cubic interpolation there is a possibility we
        # will have negative values where they should be zero. So here
        # we drive any negative values to zero.
        mult_matrix[mult_matrix < 0] = 0

        # Sum all of the values from the matrix to get the total
        # captured wave energy and convert into mega watts
        sum_we = (mult_matrix.sum() / 1000)
        energy_cap[key] = sum_we

    return energy_cap

def captured_wave_energy_to_shape(energy_cap, wave_shape_uri):
    """Adds each captured wave energy value from the dictionary
        energy_cap to a field of the shapefile wave_shape. The values are
        set corresponding to the same I,J values which is the key of the
        dictionary and used as the unique identier of the shape.

        energy_cap - A dictionary with keys (I,J), representing the
            wave energy capacity values.
        wave_shape_uri  - A uri to a point geometry shapefile to
            write the new field/values to

        returns - Nothing"""

    cap_we_field = 'CAPWE_MWHY'
    wave_shape = ogr.Open(wave_shape_uri, 1)
    wave_layer = wave_shape.GetLayer()
    # Create a new field for the shapefile
    field_def = ogr.FieldDefn(cap_we_field, ogr.OFTReal)
    wave_layer.CreateField(field_def)
    # For all of the features (points) in the shapefile, get the
    # corresponding point/value from the dictionary and set the 'capWE_Sum'
    # field as the value from the dictionary
    for feat in wave_layer:
        index_i = feat.GetFieldIndex('I')
        index_j = feat.GetFieldIndex('J')
        value_i = feat.GetField(index_i)
        value_j = feat.GetField(index_j)
        we_value = energy_cap[(value_i, value_j)]

        index = feat.GetFieldIndex(cap_we_field)
        feat.SetField(index, we_value)
        # Save the feature modifications to the layer.
        wave_layer.SetFeature(feat)
        feat = None
