import json
import ogr
import platform
import csv
import os
import re

from dbfpy import dbf

def settings_folder():
    """Return the file location of the user's settings folder.  This folder
    location is OS-dependent."""
    if platform.system() == 'Windows':
        config_folder = '~/AppData/Local/NatCap'
    else:
        config_folder = '~/.natcap/'
    return os.path.expanduser(config_folder)


class JSONHandler(object):
    def __init__(self, uri):
        object.__init__(self)
        self.uri = uri
        self.dict = None
        self._load_file()


    def _load_file(self):
        try:
            file = open(self.uri).read()
            self.dict = json.loads(file)
        except (IOError, ValueError):
            # IOError occurs if file not found
            # ValueError occurs if the file is blank (or if a JSON object could
            # not be decoded)
            self.dict = {}

    def get_attributes(self):
        if not self.dict:
            self._load_file()

        return self.dict

    def write_to_disk(self, dict):
        try:
            file = open(self.uri, mode='w+')
        except IOError:  # Thrown when self.uri doesn't exist
            os.makedirs(os.path.dirname(self.uri))
            file = open(self.uri, mode='w+')

        file.writelines(json.dumps(dict))
        file.close()

class LastRunHandler(JSONHandler):
    def __init__(self, modelname):
        uri = modelname + '_lastrun_' + platform.node() + '.json'
        JSONHandler.__init__(self, os.path.join(settings_folder(), uri))

class ResourceManager(object):
    """ResourceManager reconciles overrides supplied by the user against the
    default values saved to the internal iui_resources resource file.  It
    adheres to the ResourceInterface interface and will print messages to stdout
    when defaulting to iui's internal resources."""

    def __init__(self, user_resource_dir=''):
        """Initialize the ResourceManager instance.

            user_resource_dir=''- a python string path to the user's resource
                directory.  If no path is provided, the default resources will
                be assumed and no warning messages will be printed.

            Returns nothing."""
        super(ResourceManager, self).__init__()
        iui_dir = os.path.dirname(__file__)
        iui_resource = os.path.abspath(os.path.join(iui_dir, 'iui_resources'))
        self.defaults = ResourceHandler(iui_resource)
        self.user_resources = ResourceHandler(user_resource_dir)

        self.print_warnings = True
        if user_resource_dir == '':
            self.print_warnings = False

    def _warn(self, message):
        """Print a warning message to stdout, but only if warning messages are
        allowed.  Returns nothing."""
        if self.print_warnings:
            print message

    def icon(self, icon_key):
        """Return the appropriate icon path based on the path returned by the
        user's resource file and the path returned by the default resource file.
        Defaults are used if the specified python string key cannot be found in
        the user_resources file

            icon_key - a python string key for the desired icon.

        Returns a python string."""

        try:
            return self.user_resources.icon(icon_key)
        except KeyError:
            self._warn('Icon key %s missing from user resources using default.' %
                    icon_key)
            return self.defaults.icon(icon_key)

class ResourceHandler(JSONHandler):
    """This class allows actually handles reading a resource handler file from
    disk."""
    def __init__(self, resource_dir):
        """The constructor for the ResourceHandler class.

            resource_dir - a python string path to the folder containing the
                target resources.  Must contain a resources.json file.

        Returns an instance of ResourceHandler for the resources dir specified."""

        self.resource_dir = resource_dir
        resource_file = os.path.join(resource_dir, 'resources.json')
        super(ResourceHandler, self).__init__(resource_file)
        self.check(self.dict)

    def check(self, dictionary=None):
        """Iterate through all nested key-value pairs in this resource file and
        print an error message if the file cannot be found.  Returns nothing.
        """
        for key, value in dictionary.iteritems():
            if isinstance(value, dict):
                self.check(value)
            else:
                if isinstance(value, unicode) or isinstance(value, str):
                    # make the resource path found in json relative to the
                    # resource directory.
                    value = os.path.join(self.resource_dir, value)
                    if not os.path.exists(value):
                        print 'Resource \'%s\' was not found for key \'%s\''\
                            % (value, key)
                else:
                    print 'Resource \'%s\' should be a string.'

    def icon(self, icon_key):
        """Fetch the URI based on the icon_key.  If the key is not found, raises
        a keyError.

            icon_key - a python string key to be accessed from the resources
                file.

        Returns an absolute path to the resource."""

        icon_path = os.path.join(self.resource_dir, self.dict['icons'][icon_key])
        return os.path.abspath(icon_path)

class AbstractTableHandler(object):
    """This class provides an abstract class for specific reimplementation for
        each tabular filetype"""

    def __init__(self, uri):
        """This function initializes the AbstractTableHandler object.  The user
            is required to specify a URI to a tabular object.  In this way, a
            single AbstractTableHandler object (or one of its subclasses) will
            effectively represent a single file.

            Should a user wish to change the file URI associated with this
            instance of AbstractTableHandler, the update() function is available
            to this end.

            uri - a python string URI to a tabular file.

            returns nothing."""

        object.__init__(self)
        self.file_obj = None
        self.orig_fieldnames = {}
        self.fieldnames = []
        self.table = []
        self.mask_regexp = None
        self.mask_trim = 0
        self.update(uri)

    def __iter__(self):
        """Reimplemented, allows the user to iterate through an instance of
            AbstractTableHandler without actually returning self.table.  Having
            this function allows this class to actually be iterable."""

        # Since self.table is a list (which can be made iterable), all we need
        # to do is return the iterable version of self.table.  Voila!
        return iter(self.table)

    def update(self, uri):
        """Update the URI associated with this AbstractTableHandler object.
            Updating the URI also rebuilds the fieldnames and internal
            representation of the table.

            uri - a python string target URI to be set as the new URI of this
                AbstractTableHandler.

            Returns nothing."""

        self.uri = uri
        self._open()
        self._get_field_names()
        if self.mask_regexp != None:
            # If the user has set a mask for the fieldnames, create a dictionary
            # mapping the masked fieldnames to the original fieldnames and
            # create a new (masked) list of fieldnames according to the user's
            # mask.  Eventually, this will need to accommodate multiple forms of
            # masking ... maybe a function call inside of the comprehension?
            self.orig_fieldnames = dict((k[self.mask_trim:], v) if
                re.match(self.mask_regexp, k) else (k, v) for (k, v) in
                self.orig_fieldnames.iteritems())
            self.fieldnames = [f[self.mask_trim:] if re.match(self.mask_regexp,
                f) else f for f in self.fieldnames]

        # Now that the orig_fieldnames dict and the fieldnames list have been
        # set appropriately (masked or not), regenerate the table attribute to
        # reflect these changes to the fieldnames.
        self._get_table_list()

    def set_field_mask(self, regexp=None, trim=0):
        """Set a mask for the table's self.fieldnames.  Any fieldnames that
            match regexp will have trim number of characters stripped off the
            front.
            
            regexp=None - a python string or None.  If a python string, this
                will be a regular expression.  If None, this represents no
                regular expression.
            trim - a python int.
            
            Returns nothing."""

        self.mask_regexp = regexp
        self.mask_trim = trim
        self.update(self.uri)

    def _open(self):
        """Attempt to open the file provided by uri.

            Sets self.file_obj to be a pointer to the relevant file object."""
        pass

    def get_file_object(self):
        """Getter function for the underlying file object.  If the file object
            has not been retrieved, retrieve it before returning the file
            object.

            returns a file object."""

        if self.file_obj == None:
            self._open()
        return self.file_obj

    def get_fieldnames(self, case='lower'):
        """Returns a python list of the original fieldnames, true to their
            original case.

            case='lower' - a python string representing the desired status of the
                fieldnames.  'lower' for lower case, 'orig' for original case.

            returns a python list of strings."""

        if case == 'lower':
            return self.fieldnames
        if case == 'orig':
            return [self.orig_fieldnames[f] for f in self.fieldnames]

    def _get_field_names(self):
        """Function stub for reimplementation.

            Sets self.fieldnames to a python list of lower-case versions of
            the actual fieldnames.  Also sets self.orig_fieldnames to a python
            dictionary mapping the lower-case name of each field to its
            original, case-sensitive name."""
        pass

    def _get_table_list(self):
        """Function stub for reimplementation.

            Sets self.table to a python list of dictionaries where each
            dictionary maps lower-case column names to the appropriate value.
            """
        pass

    def get_table_dictionary(self, key_field):
        """Returns a python dictionary mapping a key value to all values in that
            particular row dictionary (including the key field).  If duplicate 
            keys are found, the are overwritten in the output dictionary.

            key_field - a python string of the desired field value to be used as
                the key for the returned dictionary.

            returns a python dictionary of dictionaries."""

        if self.table == []:
            self._get_table_list()
        return dict((row[key_field], row) for row in self.table)

    def get_table_row(self, key_field, key_value):
        """Return the first full row where the value of key_field is equivalent
            to key_value.  Raises a KeyError if key_field does not exist.

            key_field - a python string.
            key_value - a value of appropriate type for this field.

            returns a python dictionary of the row, or None if the row does not
            exist."""

        if self.table == []:
            self._get_table_list()
        for row in self.table:
            if row[key_field] == key_value:
                return row
        return None

    def get_map(self, key_field, value_field):
        """Returns a python dictionary mapping values contained in key_field to
            values contained in value_field.  If duplicate keys are found, they
            are overwritten in the output dictionary.

            This is implemented as a dictionary comprehension on top of
            self.get_table_list(), so there shouldn't be a need to reimplement
            this for each subclass of AbstractTableHandler.

            If the table list has not been retrieved, it is retrieved before
            generating the map.

            key_field - a python string.
            value_field - a python string.

            returns a python dictionary mapping key_fields to value_fields."""

        if self.table == []:
            self._get_table_list()
        return dict((row[key_field], row[value_field]) for row in self.table)

class OGRHandler(AbstractTableHandler):
    def _open(self):
        self.file_obj = ogr.Open(str(self.uri))

    def _get_field_names(self):
        shapefile = self.get_file_object()
        if shapefile != None:
            layer = shapefile.GetLayer(0)
            layer_def = layer.GetLayerDefn()

            field_list = []
            for index in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(index)
                field_list.append(field_def.GetNameRef())

            self.fieldnames = [f.lower() for f in field_list]
            self.orig_fieldnames = dict((f.lower(), f) for f in field_list)
        else:
            self.fieldnames = []
            self.orig_fieldnames = {}

class DBFHandler(AbstractTableHandler):
    def _open(self, read_only = True):
        #Passing readOnly because it's likely we only need to read the file
        #not write it.
        self.file_obj = dbf.Dbf(self.uri, readOnly = read_only)

    def _get_field_names(self):
        dbf_file = self.get_file_object()
        self.orig_fieldnames = dict((name.lower(), name) for name in
            dbf_file.fieldNames)
        self.fieldnames = [r.lower() for r in dbf_file.fieldNames]

    def _get_table_list(self):
        db_file = self.get_file_object()
        table_list = []
        for record in db_file:
            record_dict = {}
            for fieldname in self.fieldnames:
                fieldname = fieldname.lower()
                orig_fieldname = self.orig_fieldnames[fieldname]
                record_dict[fieldname] = record[orig_fieldname]
            table_list.append(record_dict)

        self.table = table_list

class CSVHandler(AbstractTableHandler):
    def _open(self):
        self.file_obj = csv.DictReader(open(self.uri))

    def _get_table_list(self):
        output_list = []
        for row in self.file_obj:
            record_dict = {}
            for fieldname in self.fieldnames:
                fieldname = fieldname.lower()
                orig_fieldname = self.orig_fieldnames[fieldname]
                record_dict[fieldname] = row[orig_fieldname]
            output_list.append(record_dict)

        self.table = output_list

    def _get_field_names(self):
        csv_file = self.get_file_object()
        if not hasattr(csv_file, 'fieldnames'):
            fieldnames = csv_file.next()
        else:
            fieldnames = csv_file.fieldnames

        self.fieldnames = [name.lower() for name in fieldnames]
        self.orig_fieldnames = dict((name.lower(), name) for name in
            fieldnames)

# Define a lookup dictionary of what filetypes are associated with a particular
# file extension.  For use with find_handler().
FILETYPES = {'.csv': CSVHandler,
             '.dbf': DBFHandler,
             '.shp': OGRHandler}

def find_handler(uri):
    """Attempt to open the file provided by uri.

            uri - a string URI to a table on disk.

        returns the appropriate file's Handler.  Returns None if an
        appropriate handler cannot be found."""

    class InvalidExtension(Exception): pass
    # determine the filetype of the URI
    base, ext = os.path.splitext(uri)
    handler = None
    try:
        # attempt to open the file with the filetype identified by the
        # extension.  Raise an exception if it can't be opened.
        handler = FILETYPES[ext.lower()](uri)
        open_file = handler.get_file_object()
        if open_file == None: raise InvalidExtension

    except KeyError, InvalidExtension:
        # if for some reason, the defined filetype doesn't exist in the
        # filetypes dictionary, loop through all of the available handlers
        for class_reference in FILETYPES.values():
            handler = class_reference(uri)
            opened_file = handler.open(uri)
            if opened_file != None: break

    return handler

