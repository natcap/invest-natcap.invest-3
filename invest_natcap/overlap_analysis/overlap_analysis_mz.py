import os
import datetime
import glob

from osgeo import ogr

from invest_natcap.overlap_analysis import overlap_analysis_mz_core

def execute(args):
    '''
    Input:
        args: A python dictionary created by the UI and passed to this method.
            It will contain the following data.
        args['workspace_dir']- The directory in which to place all resulting files,
            will come in as a string.
        args['zone_layer_loc']- A URI pointing to a shapefile with the analysis
            zones on it.
        args['overlap_data_dir_loc']- URI pointing to a directory where multiple
            shapefiles are located. Each shapefile represents an activity of
            interest for the model.
    Output:
        mz_args- The dictionary of all arguments that are needed by the
            overlap_analysis_mz_core.py class. This list of processed inputs will
            be directly passed to the core in order to create model outputs.
    '''

    mz_args = {}

    workspace = args['workspace_dir']
    output_dir = workspace + os.sep + 'Output'
    inter_dir = workspace + os.sep + 'Intermediate'
        
    if not (os.path.exists(output_dir)):
        os.makedirs(output_dir)
        
    if not (os.path.exists(inter_dir)):
        os.makedirs(inter_dir)
        
    mz_args['workspace_dir'] = args['workspace_dir']

    #We are passing in the AOI shapefile, as well as the dimension that we want the
    #raster pixels to be. 
    mz_args['zone_layer_file'] = ogr.Open(args['zone_layer_loc'])

    file_dict = get_files_dict(args['overlap_data_dir_loc'])
    mz_args['over_layer_dict'] = file_dict
    
    overlap_analysis_mz_core.execute(mz_args)

def get_files_dict(folder):
    '''Returns a dictionary of all .shp files in the folder.

        Input:
            folder- The location of all layer files. Among these, there should be
                files with the extension .shp. These will be used for all
                activity calculations.

        Returns:
            file_dict- A dictionary which maps the name (minus file extension) of
                a shapefile to the open datasource itself. The key in this dictionary
                is the name of the file (not including file path or extension), and 
                the value is the open shapefile.
    '''

    #Glob.glob gets all of the files that fall into the form .shp, and makes them
    #into a list. Then, each item in the list is added to a dictionary as an open
    #file with the key of it's filename without the extension, and that whole
    #dictionary is made an argument of the mz_args dictionary
    file_names = glob.glob(os.path.join(folder, '*.shp'))
    file_dict = {}
    
    for file in file_names:
        
        #The return of os.path.split is a tuple where everything after the final slash
        #is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes before
        #the file extension, and the second is the extension itself 
        name = os.path.splitext(os.path.split(file)[1])[0]
        file_dict[name] = ogr.Open(file)
   
    return file_dict
