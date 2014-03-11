import os
import shutil
import random
import numpy

from osgeo import ogr
from osgeo import gdal


from invest_natcap.sediment import sediment
from invest_natcap import raster_utils
from invest_natcap.optimization import optimization

DATA = os.path.join('test', 'invest-data')

def willimate_run(workspace_dir):

    args = {}
    args['workspace_dir'] = os.path.join(workspace_dir, 'base_run')

    if not os.path.exists(args['workspace_dir']):
        os.makedirs(args['workspace_dir'])
    args['dem_uri'] = os.path.join(DATA, 'Base_Data/Freshwater/dem')
    args['erosivity_uri'] = os.path.join(DATA, 'Base_Data/Freshwater/erosivity')
    args['erodibility_uri'] = os.path.join(DATA, 'Base_Data/Freshwater/erodibility')
    base_landuse_uri = os.path.join(DATA, 'Base_Data/Freshwater/landuse_90')
    args['landuse_uri'] = base_landuse_uri
    args['watersheds_uri'] = os.path.join(DATA, 'Base_Data/Freshwater/watersheds.shp')
    args['biophysical_table_uri'] = '../data/colombia_testing/Biophysical_Colombia_new.csv'
    args['threshold_flow_accumulation'] = 1000
    args['slope_threshold'] = 75.0
    args['sediment_threshold_table_uri'] = os.path.join(DATA, 'Sedimentation/input/sediment_threshold_table.csv')
    sediment.execute(args)

    sediment_export_base = os.path.join(args['workspace_dir'], 'Output', 'sed_export.tif')
    base_sediment_export = raster_utils.aggregate_raster_values_uri(
        sediment_export_base, args['watersheds_uri'], 'ws_id', 'sum').total[0]


    temp_dir = os.path.join(args['workspace_dir'], 'temp')
    for temp_variable in ['TMP', 'TEMP', 'TMPDIR']:
        try:
            old_value = os.environ[temp_variable]
        except KeyError:
            old_value = None
        os.environ[temp_variable] = temp_dir
    os.makedirs(temp_dir)

    def _reset_temp_dir():
        shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

    #######Create a mining only export lulc and export map
    only_mining_lulc_uri = os.path.join(workspace_dir, 'mining_lulc.tif')
    landuse_nodata = raster_utils.get_nodata_from_uri(args['landuse_uri'])
    mining_lulc_value = 2906
    def convert_to_mining(original_lulc):
        if original_lulc == landuse_nodata:
            return landuse_nodata
        return mining_lulc_value
    print 'creating the mining lulc'
    landuse_pixel_size = raster_utils.get_cell_size_from_uri(args['landuse_uri'])
    raster_utils.vectorize_datasets(
        [args['landuse_uri']], convert_to_mining,
        only_mining_lulc_uri, gdal.GDT_Int32, landuse_nodata,
        landuse_pixel_size, "union", dataset_to_align_index=0, 
        aoi_uri=args['watersheds_uri'])

    args['suffix'] = 'mining'
    args['landuse_uri'] = only_mining_lulc_uri
    print 'simulating the entire watershed as mining'
    sediment.execute(args)
    args.pop('suffix')
    _reset_temp_dir()
    

    ########Subtract the mining only and origina lulc map for a static permitting map
    original_export_uri = os.path.join(args['workspace_dir'], 'Output', 'sed_export.tif')
    export_nodata = raster_utils.get_nodata_from_uri(original_export_uri)
    mining_export_uri = os.path.join(args['workspace_dir'], 'Output', 'sed_export_mining.tif')
    static_impact_map_uri = os.path.join(workspace_dir, 'static_impact_map.tif')

    def sub_export(original_export, mining_export):
        if original_export == export_nodata:
            return export_nodata
        return mining_export - original_export
    print 'calculating the static impact map'
    raster_utils.vectorize_datasets(
        [original_export_uri, mining_export_uri], sub_export,
        static_impact_map_uri, gdal.GDT_Float32, export_nodata,
        landuse_pixel_size, "union", dataset_to_align_index=0, 
        aoi_uri=args['watersheds_uri'])
    _reset_temp_dir()


    ########create a random permitting polygon
    logfile = open(os.path.join(workspace_dir, 'logfile.txt'), 'w')
    for run_number in range(10000):
        permit_area = random.uniform(500,3000)
        permitting_workspace_uri = os.path.join(workspace_dir, 'random_permit_%s' % run_number)
        create_random_permitting_site(permitting_workspace_uri, args['watersheds_uri'], permit_area)

        #Create a new LULC that masks the LULC values to the new type that lie within
        #the permitting site and re-run sediment model, base new lulc on user input
        permitting_mask_uri = os.path.join(permitting_workspace_uri, 'random_permit_mask.tif')

        landuse_nodata = raster_utils.get_nodata_from_uri(args['landuse_uri'])
        landuse_pixel_size = raster_utils.get_cell_size_from_uri(args['landuse_uri'])
        def mask_op(value):
            if value == landuse_nodata:
                return landuse_nodata
            return 1.0
        print 'making the raster mask for the permitting area'

        raster_utils.vectorize_datasets(
            [args['landuse_uri']], mask_op, permitting_mask_uri, gdal.GDT_Float32, landuse_nodata,
            landuse_pixel_size, "intersection", dataset_to_align_index=0, aoi_uri=permitting_workspace_uri)

        converted_lulc_uri = os.path.join(permitting_workspace_uri, 'permitted_lulc.tif')
        #I got this from the pucallapa biophysical table
        mining_lulc_value = 2906
        def convert_lulc(original_lulc, permit_mask):
            if permit_mask == 1.0:
                return mining_lulc_value
            return original_lulc
        print 'creating the permitted lulc'
        raster_utils.vectorize_datasets(
            [base_landuse_uri, permitting_mask_uri], convert_lulc,
            converted_lulc_uri, gdal.GDT_Float32, landuse_nodata,
            landuse_pixel_size, "union", dataset_to_align_index=0, 
            aoi_uri=args['watersheds_uri'])

        args['workspace_dir'] = permitting_workspace_uri
        args['landuse_uri'] = converted_lulc_uri
        args['suffix'] = str(run_number)

        sediment.execute(args)
        _reset_temp_dir()

        sediment_export_permitting = os.path.join(permitting_workspace_uri, 'Output', 'sed_export_%s.tif' % str(run_number))

        #Lookup the amount of sediment export on the watershed polygon
        permitting_sediment_export = raster_utils.aggregate_raster_values_uri(
            sediment_export_permitting, args['watersheds_uri'], 'ws_id',
            'sum').total[0]

        static_sediment_export = raster_utils.aggregate_raster_values_uri(
            static_impact_map_uri, permitting_workspace_uri, 'id', 'sum').total[1]

        logfile.write(str(permit_area))
        logfile.write(",")
        logfile.write(str((permitting_sediment_export - base_sediment_export)/static_sediment_export))
        logfile.write(",")
        logfile.write(str(static_sediment_export))
        logfile.write(",")
        logfile.write(str(permitting_sediment_export - base_sediment_export))
        logfile.write('\n')
        logfile.flush()
    logfile.close()







def base_run(workspace_dir):
    args = {}
    args['workspace_dir'] = os.path.join(workspace_dir, 'base_run')
    if not os.path.exists(args['workspace_dir']):
        os.makedirs(args['workspace_dir'])
    args['dem_uri'] = '../Pucallpa_subset/dem_fill'
    args['erosivity_uri'] = '../Pucallpa_subset/imf_erosivity'
    args['erodibility_uri'] = '../Pucallpa_subset/erod_k'
    args['landuse_uri'] = '../Pucallpa_subset/lulc_bases'
    args['watersheds_uri'] = '../Pucallpa_subset/ws_20.shp'
    args['biophysical_table_uri'] = '../Pucallpa_subset/biophysical.csv'
    args['threshold_flow_accumulation'] = 1000
    args['slope_threshold'] = 70.0
    args['sediment_threshold_table_uri'] = '../Pucallpa_subset/sed_thresh.csv'
    #First calculate the base sediment run


    #create a random permitting polygon
    permitting_datasource_uri = os.path.join(workspace_dir, 'random_permit')
    create_random_permitting_site(permitting_datasource_uri, args['watersheds_uri'], 7000)

    #Create a new LULC that masks the LULC values to the new type that lie within
    #the permitting site and re-run sediment model, base new lulc on user input
    permitting_mask_uri = os.path.join(workspace_dir, 'random_permit_mask.tif')

    landuse_nodata = raster_utils.get_nodata_from_uri(args['landuse_uri'])
    landuse_pixel_size = raster_utils.get_cell_size_from_uri(args['landuse_uri'])
    def mask_op(value):
        if value == landuse_nodata:
            return landuse_nodata
        return 1.0
    print 'making the raster mask for the permitting area'
    raster_utils.vectorize_datasets(
        [args['landuse_uri']], mask_op, permitting_mask_uri, gdal.GDT_Float32, landuse_nodata,
        landuse_pixel_size, "intersection", dataset_to_align_index=0, aoi_uri=permitting_datasource_uri)

    converted_lulc_uri = os.path.join(workspace_dir, 'permitted_lulc.tif')
    #I got this from the pucallapa biophysical table
    mining_lulc_value = 2906
    def convert_lulc(original_lulc, permit_mask):
        if permit_mask == 1.0:
            return mining_lulc_value
        return original_lulc
    print 'creating the permitted lulc'
    raster_utils.vectorize_datasets(
        [args['landuse_uri'], permitting_mask_uri], convert_lulc,
        converted_lulc_uri, gdal.GDT_Float32, landuse_nodata,
        landuse_pixel_size, "union", dataset_to_align_index=0, 
        aoi_uri=args['watersheds_uri'])


    #prep data from sediment run
    print 'doing the base sediment run'
    sediment.execute(args)
    pixel_export_uri = os.path.join(workspace_dir, 'base_run', 'Output', 'sed_export.tif')
    pixel_export_nodata = raster_utils.get_nodata_from_uri(pixel_export_uri)

    print 'doing the permitting sediment run'
    args['workspace_dir'] = os.path.join(workspace_dir, 'permitting_run')
    args['landuse_uri'] = converted_lulc_uri
    sediment.execute(args)
    permitting_pixel_export_uri = os.path.join(workspace_dir, 'permitting_run', 'Output', 'sed_export.tif')

    pixel_export_dataset = gdal.Open(pixel_export_uri)
    pixel_export_band = pixel_export_dataset.GetRasterBand(1)
    pixel_export_array = pixel_export_band.ReadAsArray()

    permitting_pixel_export_dataset = gdal.Open(permitting_pixel_export_uri)
    permitting_pixel_export_band = pixel_export_dataset.GetRasterBand(1)
    permitting_pixel_export_array = pixel_export_band.ReadAsArray()

    permitting_export = sum(permitting_pixel_export_array[permitting_pixel_export_array != pixel_export_nodata])
    base_export = sum(pixel_export_array[pixel_export_array != pixel_export_nodata])

    export_difference = permitting_export - base_export
                         
    print permitting_export, base_export, export_difference


    closure = {'max_export': -1.0}
    #Find the max export
    def find_max_export(pixel_export):
        if pixel_export == pixel_export_nodata:
            return pixel_export_nodata
        if pixel_export > closure['max_export']:
            closure['max_export'] = pixel_export
        return 1.0
    dataset_out_uri = raster_utils.temporary_filename()
    pixel_size_out = raster_utils.get_cell_size_from_uri(pixel_export_uri)
    raster_utils.vectorize_datasets(
        [pixel_export_uri], find_max_export, dataset_out_uri, gdal.GDT_Float32,
        pixel_export_nodata, pixel_size_out, "intersection", aoi_uri=permitting_datasource_uri)
    print closure['max_export']

    #rasterize permitting_datasource_uri
    #rasterize permitting_datasource_uri
    #vectorize_datasets so that mask converts original lulc to bare soil
    #re-run sediment

    #take the difference of export from the base run minus the new run

    #output scores



def create_random_permitting_site(permitting_datasource_uri, base_watershed_shp, side_length):
    if os.path.exists(permitting_datasource_uri):
        shutil.rmtree(permitting_datasource_uri)

    if not os.path.exists(permitting_datasource_uri):
        os.makedirs(permitting_datasource_uri)

    base_datasource = ogr.Open(base_watershed_shp)
    base_layer = base_datasource.GetLayer()
    base_feature = base_layer.GetFeature(0)
    base_geometry = base_feature.GetGeometryRef()
    spat_ref = base_layer.GetSpatialRef()

    #feature_extent = [xmin, xmax, ymin, ymax]
    feature_extent = base_geometry.GetEnvelope()
    print feature_extent

    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.CreateDataSource(permitting_datasource_uri)
    uri_basename = os.path.basename(permitting_datasource_uri)
    layer_name = os.path.splitext(uri_basename)[0]
    layer = datasource.CreateLayer(layer_name, spat_ref, ogr.wkbPolygon)

    # Add a single ID field
    field = ogr.FieldDefn('id', ogr.OFTInteger)
    layer.CreateField(field)

    while True:
        poly_ring = ogr.Geometry(type=ogr.wkbLinearRing)
        bbox_width = feature_extent[1]-feature_extent[0]
        bbox_height = feature_extent[3]-feature_extent[2]

        rand_width_percent = random.random()
        xmin = feature_extent[0] + bbox_width * rand_width_percent
        xmax = xmin + side_length

        #Make it squarish
        rand_height_percent = random.random()
        ymin = feature_extent[2] + bbox_height * rand_height_percent
        ymax = ymin + side_length

        print feature_extent
        print xmin, xmax, ymin, ymax

        poly_ring.AddPoint(xmin, ymin)
        poly_ring.AddPoint(xmin, ymax)
        poly_ring.AddPoint(xmax, ymax)
        poly_ring.AddPoint(xmax, ymin)
        poly_ring.AddPoint(xmin, ymin)
        polygon = ogr.Geometry(ogr.wkbPolygon)
        polygon.AddGeometry(poly_ring)

        #See if the watershed contains the permitting polygon
        contained = base_geometry.Contains(polygon)
        print contained
        if contained:
            break

    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(polygon)
    feature.SetField(0, 1)
    layer.CreateFeature(feature)

    feature = None
    layer = None

def optimize_it(base_map_uri, aoi_uri, output_uri):
#    inverted_map_uri = raster_utils.temporary_filename()
    inverted_map_uri = './base_sediment_run/inverted.tif'
    base_map_nodata = raster_utils.get_nodata_from_uri(base_map_uri)
    pixel_size_out = raster_utils.get_cell_size_from_uri(base_map_uri)
    def invert(value):
        if value == base_map_nodata:
            return base_map_nodata
        return -value

    raster_utils.vectorize_datasets(
        [base_map_uri], invert, inverted_map_uri, gdal.GDT_Float32,
        base_map_nodata, pixel_size_out, "intersection", aoi_uri=aoi_uri)

    optimization.static_max_marginal_gain(
        inverted_map_uri, 500, output_uri, sigma=2.0)


if __name__ == '__main__':
    willimate_run('./base_sediment_run')
    #optimize_it('./base_sediment_run/base_run/Output/sed_ret_mining.tif', './base_sediment_run/random_permit_0/random_permit_0.shp', './base_sediment_run/optimal.tif')
