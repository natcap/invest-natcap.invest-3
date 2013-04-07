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
    sediment.execute(args)

    #create a random permitting polygon
    permitting_datasource_uri = os.path.join(workspace_dir, 'random_permit')
    create_random_permitting_site(permitting_datasource_uri, args['watersheds_uri'])

    #prep data from sediment run
    pixel_export_uri = os.path.join(workspace_dir, 'base_run', 'Output', 'sed_export.tif')
    pixel_export_nodata = raster_utils.get_nodata_from_uri(pixel_export_uri)

    #Find the max export
    closure = {'max_export': -1.0}
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



    #Create a new LULC that masks the LULC values to the new type that lie within
    #the permitting site and re-run sediment model, base new lulc on user input

    #take the difference of export from the base run minus the new run

    #output scores



def create_random_permitting_site(permitting_datasource_uri, base_watershed_shp):
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
        poly_width = feature_extent[1]-feature_extent[0]
        poly_height = feature_extent[3]-feature_extent[2]

        rand_width_percent = random.random()
        xmin = feature_extent[0] + poly_width * rand_width_percent
        xmax = feature_extent[1] - poly_width * random.random() * rand_width_percent

        #Make it squarish
        rand_height_percent = rand_width_percent + (0.5-random.random())*0.3
        ymin = feature_extent[2] + poly_height * rand_height_percent
        ymax = feature_extent[3] - poly_height * random.random() * rand_height_percent

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

    datasource.SyncToDisk()

if __name__ == '__main__':
    base_run('./base_sediment_run')
