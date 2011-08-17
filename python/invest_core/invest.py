"""InVEST main plugin interface module"""

import imp

def execute(model, args):
    """This function invokes the model specified, processes the arguments
    to load data structures, and invokes the underlying model.
    
    model - the name of the invest module
    args - either a JSON string or dictionary object of arguments"""

    #load the module
    module = imp.load_source(model, model + '_core.py')

    #process the args for input
    map(args, data_hander.open)

    #execute the well known name 'execute' that exists in all invest plugins
    module.execute(args)

    #process the args for output
    map(args, data_hander.close)

def supportedModels():
    """returns an array of InVEST model names"""

    return ['carbon']


