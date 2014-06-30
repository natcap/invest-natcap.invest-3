"""InVEST Coastal Protection model non-core."""

import os

from osgeo import ogr

import coastal_vulnerability_core

def execute(args):
    """This function invokes the coastal protection model given uri inputs 
        specified by the user's guide.
    
    args - a dictionary object of arguments 
       
    args['workspace_dir']     - The file location where the outputs will 
                                be written (Required)
    """

    #Add the Output directory onto the given workspace
    workspace_dir = args['workspace_dir'] + os.sep + 'output/'
    if not os.path.isdir(workspace_dir):
        os.makedirs(workspace_dir)

    coastal_protection_core.execute(args)


#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, json_args = sys.argv
    args = json.loads(json_args)
    execute(args)
