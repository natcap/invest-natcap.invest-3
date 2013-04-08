import os
import shutil
import random


from osgeo import ogr
from osgeo import gdal


from invest_natcap.sediment import sediment
from invest_natcap import raster_utils

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
    field = ogr.FieldDefn('id', ogr.OFTReal)
    layer.CreateField(field)

    while True:
        poly_ring = ogr.Geometry(type=ogr.wkbLinearRing)
        bbox_width = feature_extent[1]-feature_extent[0]
        bbox_height = feature_extent[3]-feature_extent[2]

        rand_width_percent = random.random()
        xmin = feature_extent[0] + bbox_width * rand_width_percent
        xmax = xmin + side_length * random.uniform(0.8, 1.2)

        #Make it squarish
        rand_height_percent = random.random()
        ymin = feature_extent[2] + bbox_height * rand_height_percent
        ymax = ymin + side_length * random.uniform(0.8, 1.2)

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

if __name__ == '__main__':
    base_run('./base_sediment_run')
