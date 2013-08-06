'''Core module for both overlap analysis and management zones. This function
can be used by either of the secondary modules within the OA model.'''
import glob
import os

from osgeo import ogr

def get_files_dict(folder):
    '''Returns a dictionary of all .shp files in the folder.

        Input:
            folder- The location of all layer files. Among these, there should 
                be files with the extension .shp. These will be used for all
                activity calculations.

        Returns:
            file_dict- A dictionary which maps the name (minus file extension) 
                of a shapefile to the open datasource itself. The key in this
                dictionary is the name of the file (not including file path or
                extension), and the value is the open shapefile.
    '''

    #Glob.glob gets all of the files that fall into the form .shp, and makes 
    #them into a list. Then, each item in the list is added to a dictionary as
    #an open file with the key of it's filename without the extension, and that
    #whole dictionary is made an argument of the mz_args dictionary
    dir_list = listdir(hra_args[ele])
    file_names = []
    file_names += fnmatch.filter(dir_list, '*.shp')
    file_dict = {}
    
    for file in file_names:
        
        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        name = os.path.splitext(os.path.split(file)[1])[0]
        file_dict[name] = ogr.Open(file)
   
    return file_dict

