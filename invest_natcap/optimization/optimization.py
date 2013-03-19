from osgeo import gdal
import numpy

def new_raster_from_base(base, output_uri, gdal_format, nodata, datatype, fill_value=None):
    """Create a new, empty GDAL raster dataset with the spatial references,
        dimensions and geotranforms of the base GDAL raster dataset.
        
        base - a the GDAL raster dataset to base output size, and transforms on
        output_uri - a string URI to the new output raster dataset.
        gdal_format - a string representing the GDAL file format of the 
            output raster.  See http://gdal.org/formats_list.html for a list
            of available formats.  This parameter expects the format code, such
            as 'GTiff' or 'MEM'
        nodata - a value that will be set as the nodata value for the 
            output raster.  Should be the same type as 'datatype'
        datatype - the pixel datatype of the output raster, for example 
            gdal.GDT_Float32.  See the following header file for supported 
            pixel types:
            http://www.gdal.org/gdal_8h.html#22e22ce0a55036a96f652765793fb7a4
        fill_value - (optional) the value to fill in the raster on creation
                
        returns a new GDAL raster dataset."""

    n_cols = base.RasterXSize
    n_rows = base.RasterYSize
    projection = base.GetProjection()
    geotransform = base.GetGeoTransform()
    driver = gdal.GetDriverByName(gdal_format)
    new_raster = driver.Create(output_uri.encode('utf-8'), n_cols, n_rows, 1, datatype)
    new_raster.SetProjection(projection)
    new_raster.SetGeoTransform(geotransform)
    band = new_raster.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    if fill_value != None:
        band.SetNoDataValue(fill_value)
    else:
        band.SetNoDataValue(nodata)
    band = None

    return new_raster


def static_max_marginal_gain(
	score_dataset_uri, budget, output_datset_uri, aoi_uri=None):
	"""This funciton calculates the maximum marginal gain by selecting pixels
		in a greedy fashion until the entire budget is spent.
		
		score_dataset_uri - gdal dataset to a float raster
		budget - number of pixels to select
		output_dataset_uri - the uri to an output gdal dataset of type gdal.Byte
			values are 0 if not selected, 1 if selected, and nodata if the original
			was nodata.
		aoi_uri - an area to consider selection
	
	returns nothing"""
	
	dataset = gdal.Open(score_dataset_uri)
	band = dataset.GetRasterBand(1)
	
	#TODO: use memmapped or hd5 arrays here
	array = band.ReadAsArray()
	flat_array = array.flat
	in_nodata = band.GetNoDataValue()
	ordered_indexes = numpy.argsort(flat_array)
	
	#TODO: use memmapped or hd5 arrays here
	out_nodata = 255
	output_array = numpy.empty_like(flat_array, dtype=numpy.ubyte)
	output_array[:] = out_nodata
	
	#TODO: mask aoi_uri here
	
	#Walk through the indices in reverse order
	current_index = len(ordered_indexes)
	while current_index > 0:
		current_index -= 1
		if budget <= 0: 
			break
		top_index = ordered_indexes[current_index]
		if flat_array[top_index] == in_nodata:
			continue
		output_array[top_index] = 1	
		budget -= 1
		
	print output_array
	
	out_dataset = new_raster_from_base(dataset, output_datset_uri, 'GTiff', out_nodata, gdal.GDT_Byte)
	out_band = out_dataset.GetRasterBand(1)
	output_array.shape = array.shape
	out_band.WriteArray(output_array)
static_max_marginal_gain('../../../OYNPP1.tif', 279936, 'test.tif')