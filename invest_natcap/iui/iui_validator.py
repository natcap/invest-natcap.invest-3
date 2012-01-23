import sys
import os
import re
import csv
import string

import osgeo
from osgeo import ogr
from osgeo import gdal

from invest_natcap.dbfpy import dbf
import registrar

class Validator(registrar.Registrar):
    """Validator class contains a reference to an object's type-specific checker.
        It is assumed that one single iui input element will have its own 
        validator.
        
        element - a reference to the element in question."""
        
    def __init__(self, element):
        #allElements is a pointer to a python dict: str id -> obj pointer.
        registrar.Registrar.__init__(self)

        self.element = element
        updates = {'GDAL': GDALChecker,
                   'OGR': OGRChecker,
                   'number': NumberChecker,
                   'file': FileChecker,
                   'folder': URIChecker,
                   'DBF': DBFChecker,
                   'CSV': CSVChecker}
        self.update_map(updates)
        self.init_type_checker()
        self.validateFuncs = [self.is_element_required]

    def validate(self):
        """Validate the element.  This is a two step process: first, all 
            functions in the Validator's validateFuncs list are executed.  Then,
            The validator's type checker class is invoked to actually check the 
            input against the defined restrictions.
            
            returns a string if an error is found.  Returns None otherwise."""
            
        for func in self.validateFuncs:
            error = func()
            if error != None:
                return error
        
        if self.type_checker != None:
            return self.type_checker.run_checks()
        return ''
        
    def init_type_checker(self):
        """Initialize the type checker.
        
            returns nothing."""
            
        try:
            type = self.element.attributes['validateAs']['type']
            self.type_checker = self.get_func(type)(self.element)
        except KeyError:
            self.type_checker = None

    def is_element_required(self):
        """Check to see if the element is required.  If the element is required
            but its requirements are not satisfied, return an error message.
            
            returns a string if an error is found.  Returns None otherwise."""
            
        if self.element.isRequired() and not self.element.requirementsMet():
            return 'Element is required'

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
        for check_func in self.checks:
            error = check_func()
            if error != None:
                return error
            
        for key, value in self.valid.iteritems():
            error = self.eval(key, value)
            if error != None:
                return error
        return None
        
    def get_element(self, element_id):
        return self.element.root.allElements[element_id]

class URIChecker(Checker):
    def __init__(self, element):
        Checker.__init__(self, element)
        self.uri = None
        self.add_check_function(self.check_exists)
     
    def check_exists(self):
        """Verify that the file at URI exists."""

        self.uri = self.element.value()

        if os.path.exists(self.uri) == False:
            return str('Not found')
        
class FolderChecker(URIChecker):
    def __init__(self, element):
        URIChecker.__init__(self, element)
        self.add_check_function(self.open)
    
    def open(self):
        if not os.path.isdir(self.uri):
            return 'Must be a folder'

class FileChecker(URIChecker):
    def __init__(self, element):
        URIChecker.__init__(self, element)
        
        self.uri = None
        self.add_check_function(self.open)
        
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
        file_obj = gdal.Open(str(self.uri))
        if file_obj == None:
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
        self.num_checker = NumberChecker(self.element)
    
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

            if res_attrib['type'] == 'number':
                self.verify_number(res_field, res_attrib)
            elif res_attrib['type'] == 'string':
                self.verify_string(res_field, res_attrib)

                
    def verify_number(self, res_field, res_attrib):
        """Verify that a given field conforms to numeric restrictions.
            
            res_field - a string fieldname in the DBF file.
            res_attrib - a dictionary of restrictions
            
            returns a string if an error is found.  Otherwise, returns None."""
            
        field_str = ''
        for key, value in self.res_attrib.iteritems():
            for record in range(self.file.recordCount):
                if isinstance(value, str): #if value is a fieldname
                    value = self.file[record][value]
        
                other_value = self.file[record][res_attrib[key]]
                error = self.num_checker.check_number(value, other_value, key)
                field_str += str(res_field + ': ' + error + ' at record ' + 
                                 record)
                
        if len(field_str) > 0:
            return field_str

    def verify_string(self, res_field, res_attrib):
        """Verify that a given field conforms to its string restrictions.
        
            res_field - a string fieldname in the DBF file
            res_attrib - a dictionary of restrictions
            
            returns a string if an error is found.  Otherwise, returns None """
            
        field_str = ''
        for record in range(self.file.recordCount):
            res_field_value = self.file[record][res_field]
            regexp = res_attrib['allowedValues']
            
            if not re.search(res_field_value, regexp):
                field_str += str(res_field + ' ' + error + ' at record ' + 
                                 record)
                
        if len(field_str) > 0:
            return field_str

class NumberChecker(Checker):
    def __init__(self, element):
        Checker.__init__(self, element)
        updates = {'gteq': (self.verify, self._greater_than_equal_to),
                   'greaterThan': (self.verify, self._greater_than),
                   'lteq': (self.verify, self._less_than_equal_to),
                   'lessThan': (self.verify, self._less_than)}
        self.update_map(updates)
        
    def check_number(self, a, b, op_string):
        """Check the status of two numbers based on an operation.
        
            a - a number
            b - a number
            op_string - a string index into NumberChecker.map
            
            returns a string if an error is found.  Otherwise, returns None"""
            
        tuple = self.map[op_string]
        return tuple[1](a, b)
        
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
            
        error = op(self.element.value(), other_value)
        
        if error != None:
            return error


class CSVChecker(FileChecker):
    def __init__(self, element):
        FileChecker.__init__(self, element)

        updates = {'fieldsExist': self.verify_fields_exist,
                   'restrictions': self.verify_restrictions}
        self.update_map(updates)
        print self.checks

    def open(self):
        """Attempt to open the CSV file"""

        self.file = csv.reader(open(self.uri))
        test_file = csv.reader('')

        #isinstance won't work, testing classname against empty csv classname
        if self.file.__class__ != test_file.__class__:
            return str("Must be a CSV file")

    def verify_fields_exist(self, fields):
        prefix = 'Missing fields: '
        field_str = ''

        if not hasattr(self, "fieldnames"):
            self.fieldnames = self.file.next()

        for required_field in fields:
            if required_field not in self.fieldnames:
                field_str += str(required_field)

            if len(field_str) > 0:
                return prefix + field_str

    def verify_restrictions(self, rest):
        field_str = ''
        for restriction in self.valid['restrictions']:
            res_field = restriction['field']
            res_attrib = restriction['validateAs']

            if res_attrib['type'] == 'string':
                field_str += self._verify_string(res_field, res_attrib)
            elif res_attrib['type'] == 'number':
                field_str += self._verify_is_number(res_field, res_attrib)

            if 'valuesExist' in res_attrib:
                field_str += self._verify_values_exist(res_field, res_attrib)

        if len(field_str) > 0:
            return field_str

    def _verify_is_number(self, res_field, res_attrib):
        pass

    def _verify_string(self, res_field, res_attrib):
        field_str = ''
        if not hasattr(self.file, 'fieldnames'):
            self.fieldnames = self.file.next()
        else:
            self.fieldnames = self.file.fieldnames

        index = self.fieldnames.index(res_field)
        for row_num, row in enumerate(self.file):
            res_field_value = row[index]
            regexp = res_attrib['allowedValues']

            pattern = re.compile(regexp)
            if pattern.search(res_field_value) == None:
                field_str += str(res_field + ' not valid at record ' +
                                 str(row_num) + '. ')

        return field_str

    def _verify_values_exist(self, res_field, res_attrib):
        prefix = res_field + ' missing value: '
        field_str = ''
        index = self.file.fieldnames.index(res_field)
        for required_value in res_attrib['valuesExist']:
            exists = False
            for row in self.file:
                if row[index] == required_value:
                    exists = True

            if exists == False:
                field_str += required_value + ' '

        if len(field_str) > 0:
            return field_str


    #all check functions take a single value, which is returned by the
    #element.value() function.  All check functions should perform the required
    #checks and return an error string.
    #if no error is found, the check function should return None.
