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
        
    def __init__(self, type):
        #allElements is a pointer to a python dict: str id -> obj pointer.
        registrar.Registrar.__init__(self)

        updates = {'GDAL': GDALChecker,
                   'OGR': OGRChecker,
                   'number': NumberChecker,
                   'file': FileChecker,
                   'folder': URIChecker,
                   'DBF': DBFChecker,
                   'CSV': CSVChecker}
        self.update_map(updates)
        self.init_type_checker(type)
        self.validateFuncs = []

    def validate(self, valid_dict):
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
            return self.type_checker.run_checks(valid_dict)
        return ''
        
    def init_type_checker(self, type):
        """Initialize the type checker.
        
            returns nothing."""
            
        try:
            self.type_checker = self.get_func(type)()
        except KeyError:
            self.type_checker = None

class ValidationAssembler(object):
    def __init__(self):
        object.__init__(self)
        self.primitive_keys = {'number': ['lessThan', 'greaterThan', 'lteq', 
                                          'gteq']}

    def assemble(self, value, valid_dict):
        assembled_dict = {}
        assembled_dict['value'] = value

        if valid_dict['type'] in self.primitive_keys:
            assembled_dict.update(self._assemble_primitive(valid_dict))
        else:
            if 'restrictions' in valid_dict:
                assembled_dict.update(self._assemble_complex(valid_dict))

        return assembled_dict

    def _assemble_primitive(self, valid_dict):
        assembled_dict = {}

        for attribute in self.primitive_keys[valid_dict['type']]:
            if attribute in valid_dict:
                value = valid_dict[attribute]
                if isinstance(value, str) or isinstance(value, unicode):
                    value = self._get_value(value)
                    assembled_dict[attribute] = value

        return assembled_dict

    def _assemble_complex(self, valid_dict):
        assembled_dict = {}
        assembled_dict['restrictions'] = {}

        for index, restriction in enumerate(valid_dict['restrictions']):
            if self._is_primitive(restriction):
                assembled_primitive = self._assemble_primitive(restriction)
                assembled_dict['restrictions'][index] = assembled_primitive

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
            
        for key, value in valid_dict.iteritems():
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
    
    def open(self):
        if not os.path.isdir(self.uri):
            return 'Must be a folder'

class FileChecker(URIChecker):
    def __init__(self):
        URIChecker.__init__(self)
        self.uri = None #initialize to None
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

class TableChecker(FileChecker, ValidationAssembler):
    def __init__(self):
        FileChecker.__init__(self)
        ValidationAssembler.__init__(self)
        updates = {'fieldsExist': self.verify_fields_exist,
                   'restrictions': self.verify_restrictions}
        self.update_map(updates)
        valid_assembler = base_widgets.ValidationAssembler()
        self.primitive_keys = valid_assembler.primitive_keys
        self.num_checker = NumberChecker()
        #self.str_checker = StringChecker() #to be implemented
       
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

    def _get_fieldnames(self):
        """This is a function stub for reimplementation.  Must return a list of
            strings"""
        
        return []

    def _get_field_value(self, fieldname, row_index):
        """This is a function stub for reimplementation.  Function should fetch
            the value of the given field at the specified row.  Must return a scalar.
            """

        return 0


class OGRChecker(TableChecker):
    def __init__(self, element):
        TableChecker.__init__(self)

        updates = {'layer': self.open_layer}
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
        self.num_checker = NumberChecker(self.element)

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

        if not hasattr(self.file, 'fieldnames'):
            self.fieldnames = self.file.next()
        else:
            self.fieldnames = self.file.fieldnames

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

    def _match_column_values(self, column_name, res_attrib):
        field_str = ''
        index = self.fieldnames.index(column_name)

        for row_num, row in enumerate(self.file):
            res_field_value = row[index]
            regexp = res_attrib['allowedValues']

            pattern = re.compile(regexp)
            if pattern.search(res_field_value) == None:
                field_str += str(res_field + ' not valid at record ' +
                                 str(row_num) + '. ')

        return field_str

    def _verify_is_number(self, res_field, res_attrib):
        if 'allowedValues' in res_attrib:
            return self._match_column_values(res_field, res_attrib)
        else:
            field_str = ''
            index = self.fieldnames.index(res_field)
            for key, value in res_attrib.iteritems():
                for row in self.file:
                    other_value = row[res_attrib[key]]
                    error = self.num_checker.check_number(value, other_value, key)
                    if error != None:
                        field_str = str(res_field + ': ' + error + ' at record '
                            + record)

            if len(field_str) > 0:
                return field_str

    def _verify_string(self, res_field, res_attrib):
        return self._match_column_values(res_field, res_attrib)

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
