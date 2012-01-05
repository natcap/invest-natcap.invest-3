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
        self.valid = self.element.attributes['validateAs']
        self.checks = []
        
    def add_check_function(self, func, index=None):
        if index == None:
            self.checks.append(func)
        else:
            self.checks.insert(index, func)
    
    def run_checks(self):
        for check in self.checks:
            check()
            
        #execute restriction checks in map
        
    def get_element(self, element_id):
        return self.element.root.allElements[element_id]
            
class FileChecker(Checker):
    def __init__(self, element):
        Checker.__init__(self, element)
        
        self.uri = self.element.value()
        self.add_check_function(self.checkExists)
        self.add_check_function(self.open)
    
    def checkExists(self):
        """Verify that the file at URI exists."""

        if not os.path.exists(self.uri):
            return str('File not found')
        else:
            return None
        
    def open(self):
        try:
            file_handler = open(self.uri, 'w')
            file_handler.close()
        except:
            return 'Unable to open file'
        
class GDALChecker(FileChecker):
    def open(self):
        """Attempt to open the GDAL object.  URI must exist."""
        
        gdal.PushErrorHandler('CPLQuietErrorHandler')
        fileObj = gdal.Open(str(self.uri))

        if fileObj == None:
            return str('Must be a raster that GDAL can open')

class OGRChecker(FileChecker):
    def __init__(self, element):
        FileChecker.__init__(self, element)

        updates = {'layer': self.open_layer,
                   'fieldsExist': self.verify_fields_exist}
        self.update_map(updates)
        
    def open(self):
        """Attempt to open the shapefile."""
        
        self.file = ogr.Open(str(self.uri))
        
        if not isinstance(ogrFile, osgeo.ogr.DataSource):
            return str('Shapefile not compatible with OGR')
        
    def open_layer(self):
        """Attempt to open the layer specified in self.valid."""
        
        layer_name = str(self.valid['layer'])
        self.layer = self.file.GetLayerByName(layer_name)
        
        if not isinstance(self.layer, osgeo.ogr.Layer):
            return str('Shapefile must have a layer called ' + layer_name)
    
    def verify_fields_exist(self):
        """Verify that the specified fields exist.  Runs self.open_layer as a
            precondition.
            
            returns a string listing all missing fields."""
            
        error = self.open_layer
        if error != None:
            return error
        
        layer_def = self.layer.GetLayerDefn()
        prefix = 'Missing fields: '
        field_str = ''
        for field in self.valid['fieldsExist']:
            index = layer_def.GetFieldIndex(field)
            if index == -1:
                field_str += str(field + ', ')
                
        if len(field_str) > 0:
            return prefix + field_str


class DBFChecker(FileChecker):
    def __init__(self, element):
        FileChecker.__init__(self, element)
        updates = {'fieldsExist': self.verify_fields_exist,
                   'restrictions': self.verify_restrictions}
        self.update_map(updates)
    
    def open(self):
        """Attempt to open the DBF."""
        
        self.file = dbf.Dbf(str(self.uri))
        
        if not isinstance(self.file, dbf.Dbf):
            return str('Must be a DBF file')
        
    def verify_fields_exist(self):
        prefix = 'Missing fields: '
        field_str = ''
        for field in self.valid['fieldsExist']:
            if field.upper() not in self.file.FileNames:
                field_str += str(field + ', ')
        
        if len(field_str) > 0:
            return prefix + field_str
        
    def verify_restrictions(self):
        field_str = ''
        for restriction in self.valid['restrictions']:
            res_field = restriction['field']
            res_attrib = res['validateAs']
            
#            if res_attrib['type'] == 'number':
#                for record in range
#        

#    def checkDBF(self, validateAs, uri):
#            if 'restrictions' in validateAs:
#                fieldStr = ''
#                for res in validateAs['restrictions']:
#                    res_field = res['field']
#                    res_att = res['validateAs']
#
#                    if res_att['type'] == 'number':
#                        for record in range(dbfFile.recordCount):
#                            res_field_value = dbfFile[record][res_field]
#                            comp_value = dbfFile[record][res_att['greaterThan']]
#
#                            if comp_value < res_field_value:
#                                fieldStr != str(res['field'] + ' must be greater \
#than ' + res_att['greaterThan'] + ' at record ' + record)
#
#                    elif res_att['type'] == 'string':
#                        for record in range(dbfFile.recordCount):
#                            res_field_value = dbfFile[record][res_field]
#                            regexp = res_att['allowedValues']
#
#                            if not re.search(res_field_value, regexp):
#                                fieldStr += str('Field ' + res_field + ' does \
#not match the allowed pattern at record ' + record)
#
#                if fieldStr != '':
#                    return fieldStr
#        else:
#            return fileError
#        
        
class NumberChecker(Checker):
    def __init__(self, element=None, value=None):
        Checker.__init__(self, element)
        updates = {'gteq': (self.verify, self._greater_than_equal_to),
                   'greaterThan': (self.verify, self._greater_than),
                   'lteq': (self.verify, self._less_than_equal_to),
                   'lessThan': (self.verify, self._less_than)}
        self.update_map(updates)
        
        self.value = value
        
    def _greater_than(self, a, b):
        if not a < b:
            return 'Value must be greater than ' + str(b)
    
    def _less_than(self, a, b):
        if not a < b:
            return 'Value must be less than ' + str(b)
        
    def _less_than_equal_to(self, a, b):
        if not a <= b:
            return 'Value must be less than or equal to ' + str(b)
    
    def _greater_than_equal_to(self, a, b):
        if not a >= b:
            return 'Value must be greater than or equal to ' + str(b)
        
    def get_restriction(self, key):
        tuple = self.map[key]
        return tuple[0](key, tuple[1])
        
    def verify(self, key, op):
        other_value = self.valid[key]
        
        if isinstance(other_value, str):
            other_value = self.get_element(other_value)
            
        error = op(self.value, other_value)
        
        if error != None:
            return error

    #all check functions take a single value, which is returned by the
    #element.value() function.  All check functions should perform the required
    #checks and return an error string.
    #if no error is found, the check function should return None.
