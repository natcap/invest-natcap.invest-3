"""This module provides validation functionality for the IUI package.  In a
nutshell, this module will validate a value if given a dictionary that
specifies how the value should be validated."""

import os
import re
import csv
import threading
import traceback

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

        updates = {'disabled': Checker,
                   'GDAL': GDALChecker,
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
                restriction['validateAs'] = self._assemble_primitive(field_rest)
                assembled_dict['restrictions'].append(restriction)

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
            self.value = valid_dict['value']
            for check_func in self.checks:
                error = check_func(valid_dict)
                if error != None:
                    return error

            for key, value in valid_dict.iteritems():
                if key not in self.ignore and self.map[key] not in self.checks:
                    error = self.eval(key, value)
                    if error != None:
                        return error
        except Exception as e:
            print '%s: \'%s\' encountered, for input %s passing validation.' % \
                (e.__class__.__name__, str(e), valid_dict['value'])
            print traceback.format_exc()
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

    def check_exists(self, valid_dict):
        """Verify that the file at valid_dict['value'] exists.  Reimplemented
        from URIChecker class to provide more helpful, folder-oriented error
        message."""
        self.uri = valid_dict['value']

        try:
            folder_must_exist = valid_dict['mustExist']
        except KeyError:
            # Thrown when 'mustExist' is not a key in valid_dict.
            folder_must_exist = False

        if folder_must_exist and not os.path.isdir(self.uri):
            return str('Folder must exist on disk')
        else:
            if os.path.isfile(self.uri):
                return str(self.uri + ' already exists on disk')

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
        table = self._build_table()
        for restriction in restriction_list:
            for row in table:
                value = row[restriction['field']]
                assembled_dict = self.assemble(value, restriction['validateAs'])

                error = None
                if assembled_dict['type'] == 'number':
                    error = self.num_checker.run_checks(assembled_dict)
                else:  # assume the restriction type is a string
                    error = self.str_checker.run_checks(assembled_dict)

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

                # Validate projection units if the user specifies it.
                if 'units' in layer_dict['projection']:
                    linear_units = reference.GetLinearUnits()
                    if layer_dict['projection']['units'] == 'meters':
                        if linear_units != 1.0:
                            return str('Shapefile layer %s must be projected' +
                                ' in meters') % layer_name
                    elif layer_dict['projection']['units'] == 'latLong':
                        if linear_units == 1.0:
                            return str('Shapefile layer %s must be projected' +
                                ' in lat/long') % layer_name

                # Validate whether the layer should be projected
                projection = reference.GetAttrValue('PROJECTION')
                if 'exists' in layer_dict['projection']:
                    should_be_projected = layer_dict['projection']['exists']
                    if bool(projection) != should_be_projected:
                        if not should_be_projected:
                            negate_string = 'not'
                        else:
                            negate_string = ''
                        return str('Shapefile layer %s should %s be' +
                                   'projected') % (layer_name, negate_string)

                # Validate whether the layer's projection matches the
                # specified projection
                if 'name' in layer_dict['projection']:
                    if projection != layer_dict['projection']['name']:
                        return str('Shapefile layer ' + layer_name + ' must be ' +
                            'projected as ' + layer_dict['projection']['name'])

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
        self.default_regexp = '.*'
        self.add_check_function(self.check_regexp)

        # We still need to record the allowedValues key in the values map.  It
        # won't be executed twice in self.run_checks()
        updates = {'allowedValues': self.check_regexp}
        self.update_map(updates)

        self.regexp_flags = {'ignoreCase': re.IGNORECASE,
                             'verbose': re.VERBOSE,
                             'debug': re.DEBUG,
                             'locale': re.LOCALE,
                             'multiline': re.MULTILINE,
                             'dotAll': re.DOTALL}

    def check_regexp(self, valid_dict):
        """Check an input regular expression contained in valid_dict.

            valid_dict - a python dictionary with the following structure:
            valid_dict['value'] - (required) a python string to be matched
            valid_dict['allowed_values'] - (required) a python dictionary with the
                following entries:
            valid_dict['allowed_values']['pattern'] - ('required') must match
                one of the following formats:
                    * A python string regular expression formatted according to
                      the re module (http://docs.python.org/library/re.html)
                    * A python list of values to be matched.  These are treated
                      as logical or ('|' in the built regular expression).  Note
                      that the entire input pattern will be matched if you use
                      this option.  For more fine-tuned matching, use the dict
                      described below.
                    * A python dict with the following entries:
                        'values' - (optional) a python list of strings that are
                            joined by the 'join' key to create a single regular
                            expression.  If this a 'values' list is not
                            provided, it's assumed to be ['.*'], which matches
                            all patterns.
                        'join' - (optional) the character with which to join all
                            provided values to form a single regular expression.
                            If the 'join' value is not provided, it defaults to
                            '|', the operator for logical or.
                        'sub' - (optional) a string on which string substitution
                            will be performed for all elements in the 'values'
                            list.  If this value is not provided, it defaults to
                            '^%s$', which causes the entire string to be
                            matched.  This string uses python's standard string
                            formatting operations:
                            http://docs.python.org/library/stdtypes.html#string-formatting-operations
                            but should only use a single '%s'
            valid_dict['allowed_values']['flag'] - (optional) a python string
                representing one of the python re module's available
                regexp flags.  Available values are: 'ignoreCase', 'verbose',
                'debug', 'locale', 'multiline', 'dotAll'.  If a different
                string is provided, no flags are applied to the regular
                expression matching.

            This function builds a single regular expression string (if
            necessary) and checks to see if valid_dict['value'] matches that
            string.  If not, a python string with an error message is returned.
            Otherwise, None is returned.
            """
        try:
            # Attempt to get the user's selected flag from the validation
            # dictionary.  Raises a KeyError if it isn't found.
            flag = self.regexp_flags[valid_dict['allowedValues']['flag']]
        except KeyError:
            # 0 is the python re module's way of specifying no flag.  This is
            # used if the user has not provided a regexp flag in the validation
            # dictionary.
            flag = 0

        try:
            # Attempt to build a regexp object based on the regex info.
            # Raises a KeyError if the user has not provided a regular
            # expression to use.
            valid_pattern = valid_dict['allowedValues']['pattern']

            # If the user's provided pattern is a string, we should use it
            # directly and assume it's a stright-up regular expression.
            if isinstance(valid_pattern, str):
                user_pattern = valid_pattern
            else:
                # If the user provides a data structure instead of a string, we
                # should build a regular expression from the user's information.
                try:
                    join_char = valid_pattern['join']
                except (KeyError, TypeError):
                    # KeyError thrown when 'join' key does not exist.
                    # TypeError thrown when valid_pattern is not a dict.
                    join_char = '|'

                try:
                    sub_string = valid_pattern['sub']
                except (KeyError, TypeError):
                    # KeyError thrown when 'sub' key does not exist.
                    # TypeError thrown when valid_pattern is not a dict.
                    sub_string = '^%s$'

                try:
                    value_list = valid_pattern['values']
                except KeyError:
                    # Thrown when the user does not provide a list of values
                    value_list = ['.*']
                except TypeError:
                    # Thrown when valid_pattern is not a dictionary.
                    # value_list must be a python list, so we should convert
                    # whatever is given us into a list.  Casting a list to a
                    # list results in a list.
                    value_list = list(valid_pattern)

                # Apply the user's configuration options to all values defined
                # and actually build a single regular expression string for
                # python's re module.
                rendered_list = [sub_string % r for r in value_list]
                user_pattern = join_char.join(rendered_list)
        except KeyError:
            # If the user has not provided a regular expression, we should use
            # the default regular expression instead.
            user_pattern = self.default_regexp

        pattern = re.compile(user_pattern, flag)
        value = valid_dict['value']  # the value to compare against our regex
        if pattern.match(str(value)) == None:
            return str("Value '%s' not allowed (allowed values: %s)" %
                (value, user_pattern))

class NumberChecker(PrimitiveChecker):
    def __init__(self):
        # Set numeric default regexp.  Used if user does not provide a regex
        self.default_regexp = '[0-9]*(\\.[0-9]*)?'

        PrimitiveChecker.__init__(self)
        updates = {'gteq': self.greater_than_equal_to,
                   'greaterThan': self.greater_than,
                   'lteq':  self.less_than_equal_to,
                   'lessThan':  self.less_than}
        self.update_map(updates)

    def greater_than(self, b):
        if not float(self.value) > b:
            return str(self.value) + ' must be greater than ' + str(b)

    def less_than(self, b):
        if not float(self.value) < b:
            return str(self.value) + ' must be less than ' + str(b)

    def less_than_equal_to(self, b):
        if not float(self.value) <= b:
            return str(self.value) + ' must be less than or equal to ' + str(b)

    def greater_than_equal_to(self, b):
        if not float(self.value) >= b:
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
            dialect = csv.Sniffer().sniff(open(self.uri).read())
        except csv.Error:
            return str("Must be a CSV file")

        # Now that we know the csv file is probably good, we can actually open
        # the file and save the DictReader object.
        self.file = csv.DictReader(open(self.uri))

    def _build_table(self):
        table_rows = []
        fieldnames = self._get_fieldnames()
        for record in self.file:
            table_rows.append(record)
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
