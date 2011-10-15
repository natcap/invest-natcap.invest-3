"""InVEST main plugin interface module"""

import imp, sys, os
import simplejson as json

def execute(model, args):
    """This function invokes the model specified and invokes the underlying model.
    
    model - the name of the invest module
    args - dictionary object of arguments
    
    returns nothing"""

    #load the module
    os.chdir(os.path.dirname(os.path.realpath(__file__)))    
    module = imp.load_source(model, model + '.py')

    #execute the well known name 'execute' that exists in all invest plugins
    module.execute(args)

def supportedModels():
    """returns an array of InVEST model names"""
    return ['carbon']

#This part is for command line invocation and allows json objects to be passed
#as the argument dictionary
if __name__ == '__main__':

    modulename, model, json_args = sys.argv
    args = json.loads(json_args)
    execute(model, args)
