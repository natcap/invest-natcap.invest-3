"""This module provides validation functionality for the IUI package.  In a
nutshell, this module will validate a value if given a dictionary that
specifies how the value should be validated."""

import os
import re
import csv
import threading

import osgeo
from osgeo import ogr
from osgeo import gdal

from dbfpy import dbf
import registrar

def get_fields(feature):
    """Return a dict with all fields in the given feature.
        
        feature - an OGR feature.
        
        Returns an assembled python dict with a mapping of 
        fieldname -> fieldvalue"""

    fields = {}
    for i in range(feature.GetFieldCount()):
        field_def = feature.GetFieldDefnRef(i)
        name = field_def.GetNameRef()
        value = feature.GetField(i)
        fields[name] = value

    return fields

class Validator(registrar.Registrar):
    """Validator class contains a reference to an object's type-specific
        checker.
        It is assumed that one single iui input element will have its own
        validator.

        Validation can be performed at will and is performed in a new thread to
        allow other processes (such as the UI) to proceed without interruption.

        Validation is available for a number of different values: files of
        various types (see the FileChecker and its subclasses), strings (see the
        PrimitiveChecker class) and numbers (see the NumberChecker class).

        element - a reference to the element in question."""

    def __init__(self, validator_type):
        #allElements is a pointer to a python dict: str id -> obj pointer.
        registrar.Registrar.__init__(self)

        updates = {'GDAL': GDALChecker,
                   'OGR': OGRChecker,
                   'number': NumberChecker,
                   'file': FileChecker,
                   'exists': URIChecker,
                   'folder': FolderChecker,
                   'DBF': DBFChecker,
                   'CSV': CSVChecker,
                   'string': PrimitiveChecker}
        self.update_map(updates)
        self.type_checker = self.init_type_checker(str(validator_type))
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
        """Check to see whether the validator has finished.  This is done by
        calling the active thread's is_alive() function.

        Returns a boolean.  True if the thread is alive."""

        if self.thread == None:
            return True
        return not self.thread.is_alive()

    def get_error(self):
        """Gets the error message returned by the validator.

        Returns None if no error found.  String error message if an error was
        found."""

        return self.thread.error_msg

    def init_type_checker(self, validator_type):
        """Initialize the type checker based on the input validator_type.

            validator_type - a string representation of the validator type.

            Returns an instance of a checker class if validator_type matches an
                existing checker class.  Returns None otherwise."""

        try:
            return self.get_func(validator_type)()
        except KeyError:
            return None

class ValidationThread(threading.Thread):
    """This class subclasses threading.Thread to provide validation in a
        separate thread of control.  Functionally, this allows the work of
        validation to be offloaded from the user interface thread, thus
        providing a snappier UI.  Generally, this thread is created and managed
        by the Validator class."""

    def __init__(self, validate_funcs, type_checker, valid_dict):
        threading.Thread.__init__(self)
        self.validate_funcs = validate_funcs
        self.type_checker = type_checker
        self.valid_dict = valid_dict
        self.error_msg = None

    def set_error(self, error):
        """Set the local variable error_msg to the input error message.  This
        local variable is necessary to allow for another thread to be able to
        retrieve it from this thread object.

            error - a string.

        returns nothing."""

        self.error_msg = error

    def run(self):
        """Reimplemented from threading.Thread.run().  Performs the actual work
        of the thread."""

        for func in self.validate_funcs:
            error = func()
            if error != None:
                self.set_error(error)

        if self.type_checker != None:
            error = self.type_checker.run_checks(self.valid_dict)
            self.set_error(error)

class ValidationAssembler(object):
    """This class allows other checker classes (such as the abstract
    TableChecker class) to assemble sub-elements for evaluation as primitive
    values.  In other words, if an input validation dictionary contains two
    fields in a table, the ValidationAssembler class provides a framework to
    fetch the value from the table."""

    def __init__(self):
        object.__init__(self)
        self.primitive_keys = {'number': ['lessThan', 'greaterThan', 'lteq',
                                          'gteq'],
                               'string': []}

    def assemble(self, value, valid_dict):
        """Assembles a dictionary containing the input value and the assembled
        values."""
        assembled_dict = valid_dict.copy()
        assembled_dict['value'] = value

        if valid_dict['type'] in self.primitive_keys:
            assembled_dict.update(self._assemble_primitive(valid_dict))
        else:
            if 'restrictions' in valid_dict:
                assembled_dict.update(self._assemble_complex(valid_dict))

        return assembled_dict

    def _assemble_primitive(self, valid_dict):
        """Based on the input valid_dict, this function returns a dictionary
        containing the value of the comparator defined in valid_dict."""
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
        """Check to see if a validation dictionary is a primitive, as defined by
        the keys in self.primitive_keys.

        valid_dict - a validation dictionary.

        Returns True if valid_dict represents a primitive, False if not."""
        if valid_dict['type'] in self.primitive_keys:
            return True
        return False

class Checker(registrar.Registrar):
    """The Checker class defines a superclass for all classes that actually
        perform validation.  Specific subclasses exist for validating specific
        features.  These can be broken up into two separate groups based on the
        value of the field in the UI:

            * URI-based values (such as files and folders)
                * Represented by the URIChecker class and its subclasses
            * Scalar values (such as strings and numbers)
                * Represented by the PrimitiveChecker class and its subclasses

        There are two steps to validating a user's input:
            * First, the user's input is preprocessed by looping through a list
              of operations.  Functions can be added to this list by calling
              self.add_check_function().  All functions that are added to this
              list must take a single argument, which is the entire validation
              dictionary.  This is useful for guaranteeing that a given function
              is performed (such as opening a file and saving its reference to
              self.file) before any other validation happens.

            * Second, the user's input is validated according to the
              validation dictionary in no particular order.  All functions in
              this step must take a single argument which represents the
              user-defined value for this particular key.

              For example, if we have the following validation dictionary:
                  valid_dict = {'type': 'OGR',
                                'value': '/tmp/example.shp',
                                'layers: [{layer_def ...}]}
                  The OGRChecker class would expect the function associated with
                  the 'layers' key to take a list of python dictionaries.

            """
    #self.map is used for restrictions
    def __init__(self):
        registrar.Registrar.__init__(self)
        self.checks = []
        self.ignore = ['type', 'value']
        self.value = None

    def add_check_function(self, func, index=None):
        """Add a function to the list of check functions.

            func - A function.  Must accept a single argument: the entire
                validation dictionary for this element.
            index=None - an int.  If provided, the function will be inserted
                into the check function list at this index.  If no index is
                provided, the check function will be appended to the list of
                check functions.

        returns nothing"""

        if index == None:
            self.checks.append(func)
        else:
            self.checks.insert(index, func)

    def run_checks(self, valid_dict):
        """Run all checks in their appropriate order.  This operation is done in
            two steps:
                * preprocessing
                    In the preprocessing step, all functions in the list of
                    check functions are executed.  All functions in this list
                    must take a single argument: the dictionary passed in as
                    valid_dict.

                * attribute validation
                    In this step, key-value pairs in the valid_dict dictionary
                    are evaluated in arbitrary order unless the key of a
                    key-value pair is present in the list self.ignore."""
        try:
            for check_func in self.checks:
                error = check_func(valid_dict)
                if error != None:
                    return error

            self.value = valid_dict['value']
            for key, value in valid_dict.iteritems():
                if key not in self.ignore and self.map[key] not in self.checks:
                    error = self.eval(key, value)
                    if error != None:
                        return error
        except Exception as e:
            return str(e)
        return None

class URIChecker(Checker):
    """This subclass of Checker provides functionality for URI-based inputs."""
    def __init__(self):
        Checker.__init__(self)
        self.uri = None  # initialize to none
        self.add_check_function(self.check_exists)

    def check_exists(self, valid_dict):
        """Verify that the file at valid_dict['value'] exists."""

        self.uri = valid_dict['value']

        if os.path.exists(self.uri) == False:
            return str('File not found')

class FolderChecker(URIChecker):
    """This subclass of URIChecker is tweaked to validate a folder."""
    def __init__(self):
        URIChecker.__init__(self)
        self.add_check_function(self.open)

    def check_exists(self, valid_dict):
        """Verify that the file at valid_dict['value'] exists.  Reimplemented
        from URIChecker class to provide more helpful, folder-oriented error
        message."""
        self.uri = valid_dict['value']

        if os.path.exists(self.uri) == False:
            return str('Folder not found')

    def open(self, valid_dict):
        """Check to see if the folder URI at self.uri is a folder on the
        filesystem.

        Return None if no error found, return a string if otherwise."""

        if not os.path.isdir(self.uri):
            return 'Must be a folder'

class FileChecker(URIChecker):
    """This subclass of URIChecker is tweaked to validate a file on disk.

        In contrast to the FolderChecker class, this class validates that a
        specific file exists on disk."""

    def __init__(self):
        URIChecker.__init__(self)
        self.add_check_function(self.open)

    def open(self, valid_dict):
        """Checks to see if the file at self.uri can be opened by python.

            This function can be overridden by subclasses as appropriate for the
            filetype.

            Returns an error string if the file cannot be opened.  None if
            otherwise."""

        try:
            file_handler = open(self.uri, 'w')
            file_handler.close()
        except IOError:
            return 'Unable to open file'

class GDALChecker(FileChecker):
    """This class subclasses FileChecker to provide GDAL-specific validation.
    """

    def open(self, valid_dict):
        """Attempt to open the GDAL object.  URI must exist.  This is an
        overridden FileChecker.open()

        Returns an error string if in error.  Returns none otherwise."""

        gdal.PushErrorHandler('CPLQuietErrorHandler')
        file_obj = gdal.Open(str(self.uri))
        if file_obj == None:
            return str('Must be a raster that GDAL can open')

class TableChecker(FileChecker, ValidationAssembler):
    """This class provides a template for validation of table-based files."""

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

        updates = {'layers': self.check_layers}
        self.update_map(updates)

        #self.add_check_function(self.check_layers)

        self.layer_types = {'polygons' : ogr.wkbPolygon,
                            'points'  : ogr.wkbPoint}

    def open(self, valid_dict):
        """Attempt to open the shapefile."""

        self.file = ogr.Open(str(self.uri))

        if not isinstance(self.file, osgeo.ogr.DataSource):
            return str('Shapefile not compatible with OGR')

    def check_layers(self, layer_list):
        """Attempt to open the layer specified in self.valid."""

        for layer_dict in layer_list:
            layer_name = layer_dict['name']

            #used when the engineer wants to specify a layer that is the same as
            #the filename without the file suffix.
            if isinstance(layer_name, dict):
                tmp_name = os.path.basename(self.file.GetName())
                layer_name = os.path.splitext(tmp_name)[0]

            self.layer = self.file.GetLayerByName(str(layer_name))

            if not isinstance(self.layer, osgeo.ogr.Layer):
                return str('Shapefile must have a layer called ' + layer_name)

            if 'projection' in layer_dict:
                reference = self.layer.GetSpatialRef()
                projection = reference.GetAttrValue('PROJECTION')
                if projection != layer_dict['projection']:
                    return str('Shapefile layer ' + layer_name + ' must be ' +
                        'projected as ' + layer_dict['projection'])

            if 'datum' in layer_dict:
                reference = self.layer.GetSpatialRef()
                datum = reference.GetAttrValue('DATUM')
                if datum != layer_dict['datum']:
                    return str('Shapefile layer ' + layer_name + ' must ' +
                        'have the datum ' + layer_dict['datum'])

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
            table_rows.append(get_fields(feature))

        return table_rows

class DBFChecker(TableChecker):
    def open(self, valid_dict):
        """Attempt to open the DBF."""

        self.file = dbf.Dbf(str(self.uri))

        if not isinstance(self.file, dbf.Dbf):
            return str('Must be a DBF file')

    def _get_fieldnames(self):
        return self.file.header.fields

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

    def check_regexp(self, regexp_dict):
        flag = 0
        if 'flag' in regexp_dict:
            if regexp_dict['flag'] == 'ignoreCase':
                flag = re.IGNORECASE
            elif regexp_dict['flag'] == 'verbose':
                flag = re.VERBOSE
            elif regexp_dict['flag'] == 'debug':
                flag = re.DEBUG
            elif regexp_dict['flag'] == 'locale':
                flag = re.LOCALE
            elif regexp_dict['flag'] == 'multiline':
                flag = re.MULTILINE
            elif regexp_dict['flag'] == 'dotAll':
                flag = re.DOTALL

        pattern = re.compile(regexp_dict['pattern'], flag)
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
        if not self.value > b:
            return str(self.value) + ' must be greater than ' + str(b)

    def less_than(self, b):
        if not self.value < b:
            return str(self.value) + ' must be less than ' + str(b)

    def less_than_equal_to(self, b):
        if not self.value <= b:
            return str(self.value) + ' must be less than or equal to ' + str(b)

    def greater_than_equal_to(self, b):
        if not self.value >= b:
            return str(str(self.value) + ' must be greater than or equal to ' +
                str(b))

class CSVChecker(TableChecker):
    def open(self, valid_dict):
        """Attempt to open the CSV file"""

        try:
            # Using CSV's sniffer class allows us to check to see if it's a CSV
            # that python's CSV module can detect.  If not, a csv.Error
            # exception is raised.  This method catches many more erroneous
            # files than the previous method of testing the classname of a
            # CSV.DictReader.
            dialect = csv.Sniffer().sniff(open(self.uri).read(1024))
        except csv.Error:
            return str("Must be a CSV file")

        # Now that we know the csv file is probably good, we can actually open
        # the file and save the DictReader object.
        self.file = csv.DictReader(open(self.uri))

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
        if not hasattr(self.file, 'fieldnames'):
            self.fieldnames = self.file.next()
        else:
            self.fieldnames = self.file.fieldnames

        return self.fieldnames

    #all check functions take a single value, which is returned by the
    #element.value() function.  All check functions should perform the required
    #checks and return an error string.
    #if no error is found, the check function should return None.
