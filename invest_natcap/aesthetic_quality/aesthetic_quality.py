import os
from osgeo import gdal, ogr
gdal.UseExceptions()
from invest_natcap import raster_utils

import logging

import scipy.stats
import numpy

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('aesthetic_quality')

def reclassify_quantile_dataset_uri(dataset_uri, quantile_list, dataset_out_uri, datatype_out, nodata_out):
    nodata_ds = raster_utils.get_nodata_from_uri(dataset_uri)

    memory_file_uri = raster_utils.temporary_filename()
    memory_array = raster_utils.load_memory_mapped_array(dataset_uri, memory_file_uri)
    memory_array_flat = memory_array.reshape((-1,))
    
    quantile_breaks = [0]
    min_value = 1
    max_value = 32767
    for quantile in quantile_list:
        quantile_breaks.append(scipy.stats.scoreatpercentile(memory_array_flat, quantile, (min_value, max_value)))

    LOGGER.debug('quantile_breaks %s' % quantile_breaks)
    def reclass(value):
        if value == nodata_ds:
            return nodata_out
        else:
            for new_value,quantile_break in enumerate(quantile_breaks):
                if value <= quantile_break:
                    return new_value
        raise ValueError, "Value was not within quantiles."

    cell_size = raster_utils.get_cell_size_from_uri(dataset_uri)
    
    raster_utils.vectorize_datasets([dataset_uri],
                                    reclass,
                                    dataset_out_uri,
                                    datatype_out,
                                    nodata_out,
                                    cell_size,
                                    "union",
                                    dataset_to_align_index=0)

    raster_utils.calculate_raster_stats_uri(dataset_out_uri)

def get_data_type_uri(ds_uri):
    raster_ds = gdal.Open(ds_uri)
    raster_data_type = raster_ds.GetRasterBand(1).DataType
    raster_ds = None

    return raster_data_type

def viewshed(dem_uri, structure_uri, z_factor, curvature_correction, refraction, visible_feature_count_uri, cell_size, aoi_prj_uri):
    src_filename = "/home/mlacayo/Desktop/aq_tif/dem_vs.tif"
    dst_filename = visible_feature_count_uri
    
    src_ds = gdal.Open( src_filename )
    driver = gdal.GetDriverByName("GTiff")
    dst_ds = driver.CreateCopy( dst_filename, src_ds, 0 )

    # Once we're done, close properly the dataset
    dst_ds = None
    src_ds = None

def execute(args):
    """DOCSTRING"""
    LOGGER.info("Start Aesthetic Quality Model")

    #create copy of args
    aq_args=args.copy()

    #validate input
    LOGGER.debug("Validating parameters.")
    dem_cell_size=raster_utils.get_cell_size_from_uri(args['dem_uri'])
    LOGGER.debug("DEM cell size: %f" % dem_cell_size)
    if aq_args['cell_size'] < dem_cell_size:
        raise ValueError, "The cell size cannot be downsampled below %f" % dem_cell_size

    if not os.path.isdir(args['workspace_dir']):
        os.makedirs(args['workspace_dir'])

    #local variables
    LOGGER.debug("Setting local variables.")
    z_factor=1
    curvature_correction=aq_args['refraction']

    aoi_prj_uri=os.path.join(aq_args['workspace_dir'],"aoi_prj.shp")
    visible_feature_count_uri=os.path.join(aq_args['workspace_dir'],"vshed.tif")
    visible_feature_quality_uri=os.path.join(aq_args['workspace_dir'],"vshed_qual.tif")
    viewshed_dem_uri=os.path.join(aq_args['workspace_dir'],"dem_vs.tif")
    viewshed_dem_reclass_uri=os.path.join(aq_args['workspace_dir'],"dem_vs_re.tif")
    pop_stats_uri=os.path.join(aq_args['workspace_dir'],"populationStats.html")

    #clip DEM by AOI and reclass
    LOGGER.info("Clipping DEM by AOI.")

    LOGGER.debug("Saving projected AOI to %s", aoi_prj_uri)
    output_wkt = raster_utils.get_dataset_projection_wkt_uri(aq_args['dem_uri'])    
    raster_utils.reproject_datasource_uri(aq_args['aoi_uri'], output_wkt, aoi_prj_uri)
    
    LOGGER.debug("Clipping DEM by projected AOI.")
    raster_utils.clip_dataset_uri(aq_args['dem_uri'], aoi_prj_uri, viewshed_dem_uri, False)

    LOGGER.info("Reclassifying DEM to account for water at sea-level and resampling to specified cell size.")
    LOGGER.debug("Reclassifying DEM so negative values zero and resampling to save on computation.")

    nodata_dem = raster_utils.get_nodata_from_uri(aq_args['dem_uri'])

    def no_zeros(value):
        if value == nodata_dem:
            return nodata_dem
        elif value < 0:
            return 0
        else:
            return value

    raster_utils.vectorize_datasets([viewshed_dem_uri],
                                    no_zeros,
                                    viewshed_dem_reclass_uri,
                                    get_data_type_uri(viewshed_dem_uri),
                                    nodata_dem,
                                    aq_args["cell_size"],
                                    "union")
    
    #calculate viewshed
    LOGGER.info("Calculating viewshed.")
    viewshed(aq_args['dem_uri'],
                          aq_args['structure_uri'],
                          z_factor,
                          curvature_correction,
                          aq_args['refraction'],
                          visible_feature_count_uri,
                          aq_args['cell_size'],
                          aoi_prj_uri)

    LOGGER.info("Ranking viewshed.")
    #rank viewshed
    nodata_out = -1
    quantile_list = [25,50,75,100]
    datatype_out = gdal.GDT_Int32
    reclassify_quantile_dataset_uri(visible_feature_count_uri, quantile_list, visible_feature_quality_uri, datatype_out, nodata_out)

    #tabulate population impact
    LOGGER.info("Tabulating population impact.")
    LOGGER.debug("Tabulating unaffected population.")
    nodata_pop = raster_utils.get_nodata_from_uri(aq_args["pop_uri"])
    nodata_visible_feature_count = raster_utils.get_nodata_from_uri(visible_feature_count_uri)

    pop = gdal.Open(aq_args["pop_uri"])
    #LOGGER.debug(pop)
    pop_band = pop.GetRasterBand(1)
    #LOGGER.debug(pop_band)
    vs = gdal.Open(visible_feature_count_uri)
    vs_band = vs.GetRasterBand(1)

    affected_pop = 0
    unaffected_pop = 0
    for row_index in range(vs_band.YSize):
        pop_row = pop_band.ReadAsArray(0, row_index, pop_band.XSize, 1)
        #LOGGER.debug(pop_row)
        vs_row = vs_band.ReadAsArray(0, row_index, vs_band.XSize, 1)

        pop_row[pop_row == nodata_pop]=0.0
        vs_row[vs_row == nodata_visible_feature_count]=-1

        affected_pop += numpy.sum(pop_row[vs_row > 0])
        unaffected_pop += numpy.sum(pop_row[vs_row == 0])

    pop_band = None
    pop = None
    vs_band = None
    vs = None

    table="""
    <html>
    <title>Marine InVEST</title>
    <center><H1>Aesthetic Quality Model</H1><H2>(Visual Impact from Objects)</H2></center>
    <br><br><HR><br>
    <H2>Population Statistics</H2>

    <table border="1", cellpadding="0">
    <tr><td align="center"><b>Number of Features Visible</b></td><td align="center"><b>Population (estimate)</b></td></tr>
    <tr><td align="center">None visible<br> (unaffected)</td><td align="center">%i</td>
    <tr><td align="center">1 or more<br>visible</td><td align="center">%i</td>
    </table>
    </html>
    """

    outfile = open(pop_stats_uri, 'w')
    outfile.write(table % (unaffected_pop, affected_pop))
    outfile.close()

    #perform overlap analysis
    LOGGER.debug("Performing overlap analysis.")
