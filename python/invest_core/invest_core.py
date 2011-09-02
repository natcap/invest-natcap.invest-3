"""InVEST main plugin interface module"""

import imp, sys, os
try:
    import json
except ImportError:
    import simplejson as json
import data_handler

def execute(model, args):
    """This function invokes the model specified, processes the arguments
    to load data structures, and invokes the underlying model.
    
    model - the name of the invest module
    args - either a JSON string or dictionary object of arguments"""

    #load the module
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    module = imp.load_source(model, model + '.py')

    #process the args for input
    for key in ('lulc_cur', 'lulc_fut', 'carbon_pools'):
        args[key] = data_handler.open(value)

    #process the args for output
    for key in ('seq_cur', 'seq_fut', 'seq_delta', 'seq_value'):
        args[key] = data_handler.mimic(args['lulc_cur'], args[key])

    #execute the well known name 'execute' that exists in all invest plugins
    module.execute(args)

    #process the args for output
    map(data_handler.close, args)

def supportedModels():
    """returns an array of InVEST model names"""

    return ['carbon']


#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    print sys.argv
    modulename, model, json_args = sys.argv
    args = json.loads(json_args)
    execute(model, args)
