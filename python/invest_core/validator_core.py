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