"""This module contains general purpose validation functions useful for
    InVEST model validators."""


import os

def checkArgsKeys(argsDict, argsList, outList):
    """Verify that all keys in argsList exist in argsDict.  Append an error
        message to outList if not.
        
        argsDict - a python dictionary mapping string keys -> arbitrary values
        argsList - a python list of keys to verify in argsDict
        outList  - a python list (for appending errors)
        
        returns nothing."""
        
    for argument in argsList:
        if argument not in argsDict:
            outList.append('Missing parameter: ' + argument)
            
def checkOutputDir(uri, out):
    """Verify that the given directory exists and is writeable.  Append error 
        messages to output list if not.
        
        uri - a python string representing the uri to the target folder
        out - a python list (for appending errors)
        
        returns nothing."""
        
    prefix = 'Output folder: ' + uri
    if not os.path.isdir(uri):
        out.append(prefix + ' not found or is not a folder.')
    else:
        #Determine if output dir is writable
        if not os.access(uri, os.W_OK):
            out.append(prefix + ' must be writeable.')