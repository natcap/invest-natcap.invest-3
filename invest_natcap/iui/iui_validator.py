import sys
import os
import re
import csv
import string
import threading

import osgeo
from osgeo import ogr
from osgeo import gdal

from invest_natcap.dbfpy import dbf
from invest_natcap.carbon import carbon_core
import registrar

class Validator(registrar.Registrar):
    """Validator class contains a reference to an object's type-specific checker.
        It is assumed that one single iui input element will have its own 
        validator.
        
        element - a reference to the element in question."""
        
    def __init__(self, type):
        #allElements is a pointer to a python dict: str id -> obj pointer.
        registrar.Registrar.__init__(self)

        updates = {'GDAL': GDALChecker,
                   'OGR': OGRChecker,
                   'number': NumberChecker,
                   'file': FileChecker,
                   'folder': URIChecker,
                   'DBF': DBFChecker,
                   'CSV': CSVChecker,
                   'string': PrimitiveChecker}
        self.update_map(updates)
        self.init_type_checker(str(type))
        self.validate_funcs = []
        self.thread = None

    def validate(self, valid_dict):
        """Validate the element.  This is a two step process: first, all 
            functions in the Validator's validateFuncs list are executed.  Then,
            The validator's type checker class is invoked to actually check the 
            input against the defined restrictions.
           
            Note that this is done in a separate thread.

            returns a string if an error is found.  Returns None otherwise."""
      
        if self.thread == None or not self.thread.is_alive():
           self.thread = ValidationThread(self.validate_funcs,
                self.type_checker, valid_dict)

        self.thread.start()

    def thread_finished(self):
        return not self.thread.is_alive()

    def get_error(self):
        return self.thread.error_msg

    def init_type_checker(self, type):
        """Initialize the type checker.
        
            returns nothing."""
        
        try:
            self.type_checker = self.get_func(type)()
        except KeyError:
            self.type_checker = None

class ValidationThread(threading.Thread):
    def __init__(self, validate_funcs, type_checker, valid_dict):
        threading.Thread.__init__(self)
        self.validate_funcs = validate_funcs
        self.type_checker = type_checker
        self.valid_dict = valid_dict
        self.error_msg = None

    def set_error(self, error):
        self.error_msg = error

    def run(self):
        for func in self.validate_funcs:
            error = func()
            if error != None:
                self.set_error(error)

        if self.type_checker != None:
            error = self.type_checker.run_checks(self.valid_dict)
            self.set_error(error)

class ValidationAssembler(object):
    def __init__(self):
        object.__init__(self)
        self.primitive_keys = {'number': ['lessThan', 'greaterThan', 'lteq', 
                                          'gteq'],
                               'string': []}

    def assemble(self, value, valid_dict):
        assembled_dict = valid_dict.copy()
        assembled_dict['value'] = value

        if valid_dict['type'] in self.primitive_keys:
            assembled_dict.update(self._assemble_primitive(valid_dict))
        else:
            if 'restrictions' in valid_dict:
                assembled_dict.update(self._assemble_complex(valid_dict))

        return assembled_dict

    def _assemble_primitive(self, valid_dict):
        assembled_dict = valid_dict.copy()
        for attribute in self.primitive_keys[valid_dict['type']]:
            if attribute in valid_dict:
                value = valid_dict[attribute]
                if isinstance(value, str) or isinstance(value, unicode):
                    value = self._get_value(value)
                    assembled_dict[attribute] = value

        return assembled_dict

    def _assemble_complex(self, valid_dict):
        assembled_dict = valid_dict.copy()
        assembled_dict['restrictions'] = []

        for restriction in valid_dict['restrictions']:
            field_rest = restriction['validateAs']
            if self._is_primitive(field_rest):
                assembled_primitive = self._assemble_primitive(field_rest)
                assembled_dict['restrictions'].append(assembled_primitive)

        return assembled_dict

    def _get_value(self, id):
        """Function stub for reimplementation.  Should return the value of the
        element identified by id, where the element itself depends on the
        context."""

        return 0

    def _is_primitive(self, valid_dict):
        if valid_dict['type'] in self.primitive_keys:
            return True
        return False

class Checker(registrar.Registrar):
    #self.map is used for restrictions
    def __init__(self):
        registrar.Registrar.__init__(self)
        self.checks = []
        self.ignore = ['type', 'value']
        
    def add_check_function(self, func, index=None):
        if index == None:
            self.checks.append(func)
        else:
            self.checks.insert(index, func)
    
    def run_checks(self, valid_dict):
        for check_func in self.checks:
            error = check_func(valid_dict)
            if error != None:
                return error
        
        self.value = valid_dict['value']
        for key, value in valid_dict.iteritems():
            if key not in self.ignore:
                error = self.eval(key, value)
                if error != None:
                    return error
        return None
        
class URIChecker(Checker):
    def __init__(self):
        Checker.__init__(self)
        self.uri = None #initialize to none
        self.add_check_function(self.check_exists)
     
    def check_exists(self, valid_dict):
        """Verify that the file at valid_dict['value'] exists."""

        self.uri = valid_dict['value']

        if os.path.exists(self.uri) == False:
            return str('Not found')
        
class FolderChecker(URIChecker):
    def __init__(self):
        URIChecker.__init__(self)
        self.add_check_function(self.open)
    
    def open(self, valid_dict):
        if not os.path.isdir(self.uri):
            return 'Must be a folder'

class FileChecker(URIChecker):
    def __init__(self):
        URIChecker.__init__(self)
        self.uri = None #initialize to None
        self.add_check_function(self.open)
        
    def open(self, valid_dict):
        try:
            file_handler = open(self.uri, 'w')
            file_handler.close()
        except:
            return 'Unable to open file'
        
class GDALChecker(FileChecker):
    def open(self, valid_dict):
        """Attempt to open the GDAL object.  URI must exist."""

        gdal.PushErrorHandler('CPLQuietErrorHandler')
        file_obj = gdal.Open(str(self.uri))
        if file_obj == None:
            return str('Must be a raster that GDAL can open')

class TableChecker(FileChecker, ValidationAssembler):
    def __init__(self):
        FileChecker.__init__(self)
        ValidationAssembler.__init__(self)
        updates = {'fieldsExist': self.verify_fields_exist,
                   'restrictions': self.verify_restrictions}
        self.update_map(updates)
        self.num_checker = NumberChecker()
        self.str_checker = PrimitiveChecker()
       
    def verify_fields_exist(self, field_list):
        """This is a function stub for reimplementation.  field_list is a python
        list of strings where each string in the list is a required fieldname.
        List order is not validated.  Returns the error string if an error is
        found.  Returns None if no error found."""
        
        available_fields = self._get_fieldnames()
        for required_field in field_list:
            if required_field not in available_fields:
                return str('Required field: ' + required_field + ' not found')

    def verify_restrictions(self, restriction_list):
        for restriction in restriction_list:
            for row in self._build_table():
                assembled_dict = {}
                value = row[restriction['field']]
                assembled_dict = self.assemble(value, restriction['validateAs'])
                
                if row['type'] == 'number':
                    error = self.num_checker(assembled_dict)
                elif row['type'] == 'string':
                    error = self.str_checker(assembled_dict)

                if error != None and error != '':
                    return error
                
    def _build_table(self):
        """This is a function stub for reimplementation.  Must return a list of
        dictionaries, where the keys to each dictionary are the fieldnames."""
        
        return [{}]

    def _get_value(self, fieldname):
        """This is a function stub for reimplementation.  Function should fetch
            the value of the given field at the specified row.  Must return a scalar.
            """

        return 0
    
    def _get_fieldnames(self):
        """This is a function stub for reimplementation.  Function should fetch
            a python list of strings where each string is a fieldname in the
            table."""

        return []

class OGRChecker(TableChecker):
    def __init__(self):
        TableChecker.__init__(self)

        updates = {'layer': self.open_layer}
        self.update_map(updates)

        self.add_check_function(self.open_layer)

        self.layer_types = {'polygons' : ogr.wkbPolygon,
                            'points'  : ogr.wkbPoint}
        
    def open(self, valid_dict):
        """Attempt to open the shapefile."""

        self.file = ogr.Open(str(self.uri))
        
        if not isinstance(ogrFile, osgeo.ogr.DataSource):
            return str('Shapefile not compatible with OGR')

    def open_layer(self, valid_dict):
        """Attempt to open the layer specified in self.valid."""
       
        layer_dict = valid_dict['layer']

        layer_name = str(layer_dict['name'])
        self.layer = self.file.GetLayerByName(layer_name)
        
        if not isinstance(self.layer, osgeo.ogr.Layer):
            return str('Shapefile must have a layer called ' + layer_name)
   
    def _check_layer_type(self, type_string):
        for feature in self.layer:
            geometry = feature.GetGeometryRef()
            geom_type = geometry.GetGeometryType()

            if geom_type != self.layer_types[type_string]:
                return str('Not all features are ' + type_string)

    def _get_fieldnames(self):
        layer_def = self.layer.GetLayerDefn()
        num_fields = layer_def.GetFieldCount()

        field_list = []
        for index in range(num_fields):
            field_def = layer_def.GetFieldDefn(index)
            field_list.append(field_def.GetNameRef())

        return field_list

    def _build_table(self):
        table_rows = []
        for feature in self.layer:
            table_rows.append(carbon_core.getFields(feature))

        return table_rows
                
class DBFChecker(TableChecker):
    def open(self):
        """Attempt to open the DBF."""
        
        self.file = dbf.Dbf(str(self.uri))
        
        if not isinstance(self.file, dbf.Dbf):
            return str('Must be a DBF file')
      
    def _get_fieldnames(self):
        return self.file.fieldNames()

    def _build_table(self):
        table_rows = []

        for record in range(self.file.recordCount):
            row = {}
            for fieldname in self._get_fieldnames():
                row[fieldname] = self.file[record][fieldname]
            
            table_rows.append(row)

        return table_rows

class PrimitiveChecker(Checker):
    def __init__(self):
        Checker.__init__(self)
        updates = {'allowedValues': self.check_regexp}
        self.update_map(updates)

    def check_regexp(self, regexp):
        pattern = re.compile(regexp)
        if pattern.match(self.value) == None:
            return str(self.value + " value not allowed")

class NumberChecker(PrimitiveChecker):
    def __init__(self):
        PrimitiveChecker.__init__(self)
        updates = {'gteq': self.greater_than_equal_to,
                   'greaterThan': self.greater_than,
                   'lteq':  self.less_than_equal_to,
                   'lessThan':  self.less_than}
        self.update_map(updates)
        
    def greater_than(self, b):
        if not self.value < b:
            return 'Value must be greater than ' + str(b)
    
    def less_than(self, b):
        if not self.value < b:
            return 'Value must be less than ' + str(b)
        
    def less_than_equal_to(self, b):
        if not self.value <= b:
            return 'Value must be less than or equal to ' + str(b)
    
    def greater_than_equal_to(self, b):
        if not self.value >= b:
            return 'Value must be greater than or equal to ' + str(b)
        
class CSVChecker(TableChecker):
    def open(self, valid_dict):
        """Attempt to open the CSV file"""

        self.file = csv.DictReader(open(self.uri))
        test_file = csv.DictReader('')

        #isinstance won't work, testing classname against empty csv classname
        if self.file.__class__ != test_file.__class__:
            return str("Must be a CSV file")

    def _build_table(self):
        table_rows = []
        fieldnames = self._get_fieldnames()
        for record in self.file:
            row = {}
            for field_name, value in zip(fieldnames, record):
                row[field_name] = value
    
            table_rows.append(row)
        return table_rows

    def _get_fieldnames(self):
        if not hasattr(self, 'fieldnames'):
            if not hasattr(self.file, 'fieldnames'):
                self.fieldnames = self.file.next()
            else:
                self.fieldnames = self.file.fieldnames
        
        return self.fieldnames

    #all check functions take a single value, which is returned by the
    #element.value() function.  All check functions should perform the required
    #checks and return an error string.
    #if no error is found, the check function should return None.
