import os
import shutil
import random


from osgeo import ogr

from invest_natcap.sediment import sediment

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
    pixel_export_uri = os.path.join(workspace_dir, 'base_run', 'Output', 'sed_export.tif')

    

def create_random_permitting_site(workspace_dir, base_watershed_shp):
    permitting_datasource_uri = os.path.join(workspace_dir,'random_permit')
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

        rand_height_percent = random.random()
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

    return




    #create a new ogr shapefile with the same projection as base_watershed_shp and save in workspace_idr
    base_datasource = ogr.Open(base_watershed_shp)
    esri_driver = ogr.GetDriverByName('ESRI Shapefile')

    datasource_copy = esri_driver.CopyDataSource(base_datasource, permitting_datasource_uri)
    layer = datasource_copy.GetLayer(0)
    print layer
    #get extents of base_watershed_shp

    #make a square of size about 1-10% of the watershed and randomly center it

    #reject if it is outside the watershed, accept otherwise



if __name__ == '__main__':
    create_random_permitting_site('permitting_dir', '../Pucallpa_subset/sws_20.shp')
#    base_run('./base_sediment_run')
