import sys
import os
import re

import osgeo
from osgeo import ogr
from osgeo import gdal

from invest_natcap.dbfpy import dbf
import registrar

class Validator():
    """Notes on subclassing:
    
        self.lookup
        ==================================
        Functions added to the dictionary self.lookup must accept one argument:
        the output of element.value().
        
        self.validateFuncs
        ==================================
        Functions added to the python list self.validateFuncs must accept the
        following arguments:
        
          id - the string identifier of the element
          element - the pointer to the element
          failed - a pointer to a python list.  This list has elements that are
            tuples with the following structure: (element pointer, error message string)
            
        """
    def __init__(self, allElements):
        #allElements is a pointer to a python dict: str id -> obj pointer.
        self.typeLookup = {'GDAL': self.checkGDAL,
                           'OGR': self.checkOGR,
                           'number': self.checkNumber,
                           'file': self.checkExists,
                           'DBF': self.checkDBF}
        self.allElements = allElements
        self.validateFuncs = [self.elementIsRequired, self.validateAs]

    def checkElement(self, element):
        failed = []
        for func in self.validateFuncs:
            func(element.attributes['id'], element, failed)

        return failed

    def checkType(self, validateAs, value):
        return self.typeLookup[validateAs['type']](validateAs, value)

    def elementIsRequired(self, id, element, failed):
        if element.isRequired() and not element.requirementsMet():
            errorMsg = 'Element is required'
            failed.append((element, errorMsg))

    def validateAs(self, id, element, failed):
        if 'validateAs' in element.attributes and element.isEnabled():
            errorMsg = self.checkType(element.attributes['validateAs'], element.value())
            if errorMsg != None:
                failed.append((element, errorMsg))

    def checkAll(self):
        """Ensure that all elements pass specified validation (validation functions
            are defined in self.validateFuncs)  Subclasses of Validator may 
            modify local versions of Validator.validateFuncs as appliccable.
        
            Functions in self.validateFuncs list must accept the following args:
              - id = the string id of the element
              - element = a pointer to the element
              - failed = a pointer to a list
        
            returns a list of tuples (element pointer, error message string)"""

        failed = []
        for id, element in self.allElements.iteritems():
            for function in self.validateFuncs:
                function(id, element, failed)

        return failed

    def checkExists(self, validateAs, uri):
        """Verify that the file at URI exists."""

        if not os.path.exists(uri):
            return str(uri + ': File not found')
        else:
            return None

class Checker(registrar.Registrar):
    #self.map is used for restrictions
    def __init__(self, element):
        registrar.Registrar.__init__(self)
        self.element = element
        self.checks = []
        
    def add_check_function(self, func, index=None):
        if index == None:
            self.checks.append(func)
        else:
            self.checks.insert(index, func)
            
    def run_checks(self):
        for check in self.checks:
            check()
            
class FileChecker(Checker):
    def __init__(self, element):
        Checker.__init__(self, element)
        
        self.uri = self.element.value()
        self.add_check_function(self.checkExists)
    
    def checkExists(self):
        """Verify that the file at URI exists."""

        if not os.path.exists(self.uri):
            return str('File not found')
        else:
            return None
        
class GDALChecker(FileChecker):
    def __init__(self, element):
        FileChecker.__init__(self, element)
        
        self.add_check_function(self.open)
        
    def open(self):
        """Attempt to open the GDAL object.  URI must exist."""
        
        gdal.PushErrorHandler('CPLQuietErrorHandler')
        fileObj = gdal.Open(str(self.uri))

        if fileObj == None:
            return str('Must be a raster that GDAL can open')



    def checkNumber(self, validateAs, value):
        if 'gteq' in validateAs:
            otherValue = validateAs['gteq']

            if isinstance(otherValue, str):
                otherValue = self.allElements[otherValue].value()

            if value < otherValue:
                return str('Value must be greater than or equal to ' + str(otherValue))

        if 'greaterThan' in validateAs:
            otherValue = validateAs['greaterThan']

            if isinstance(otherValue, str):
                otherValue = self.allElements[otherValue].value()

            if value <= otherValue:
                return str('Value must be greater than ' + str(otherValue))

        if 'lteq' in validateAs:
            otherValue = validateAs['lteq']

            if isinstance(otherValue, str):
                otherValue = self.allElements[otherValue].value()

            if value > otherValue:
                return str('Value must be less than or equal to ' + str(otherValue))

        if 'lessThan' in validateAs:
            otherValue = validateAs['lessThan']

            if isinstance(otherValue, str):
                otherValue = self.allElements[otherValue].value()

            if value >= otherValue:
                return str('Value must be less than ' + str(otherValue))

    def checkDBF(self, validateAs, uri):
        fileError = self.checkExists(validateAs, uri)
        if not fileError:
            try:
                dbfFile = dbf.Dbf(str(uri))
            except:
                return str(uri + ' is not a DBF file')

            if not isinstance(dbfFile, dbf.Dbf):
                return str(uri + ' is not a DBF file')

            if 'fieldsExist' in validateAs:
                fieldStr = ''
                for field in self.validateAs['fieldsExist']:
                    if field.upper() not in dbfFile.FileNames:
                        fieldStr += str(field + ' missing from ' + str(uri))
                if fieldStr != '':
                    return fieldStr

            if 'restrictions' in validateAs:
                fieldStr = ''
                for res in validateAs['restrictions']:
                    res_field = res['field']
                    res_att = res['validateAs']

                    if res_att['type'] == 'number':
                        for record in range(dbfFile.recordCount):
                            res_field_value = dbfFile[record][res_field]
                            comp_value = dbfFile[record][res_att['greaterThan']]

                            if comp_value < res_field_value:
                                fieldStr != str(res['field'] + ' must be greater \
than ' + res_att['greaterThan'] + ' at record ' + record)

                    elif res_att['type'] == 'string':
                        for record in range(dbfFile.recordCount):
                            res_field_value = dbfFile[record][res_field]
                            regexp = res_att['allowedValues']

                            if not re.search(res_field_value, regexp):
                                fieldStr += str('Field ' + res_field + ' does \
not match the allowed pattern at record ' + record)

                if fieldStr != '':
                    return fieldStr
        else:
            return fileError

    def checkOGR(self, validateAs, uri):
        fileError = self.checkExists(validateAs, uri)
        if not fileError:
            print 'ogr'
            ogrFile = ogr.Open(str(uri))

            if not isinstance(ogrFile, osgeo.ogr.DataSource):
                return str(uri + ' is not a shapefile that OGR can open')

            if 'layer' in validateAs:
                layer = ogrFile.GetLayerByName(str(validateAs['layer']))

                if not isinstance(layer, osgeo.ogr.Layer):
                    return str(uri + ' must have a layer called ' +
                               str(validateAs['layer']))

                if 'fieldsExist' in validateAs:
                    layer_def = layer.GetLayerDefn()
                    fieldStr = ''
                    for field in validateAs['fieldsExist']:
                        index = layer_def.GetFieldIndex(field)
                        if index == -1:
                            fieldStr += str(uri + ' : field ' + field + ' must exist')
                    if fieldStr != '':
                        return fieldStr
        else:
            return fileError

    #all check functions take a single value, which is returned by the
    #element.value() function.  All check functions should perform the required
    #checks and return an error string.
    #if no error is found, the check function should return None.
