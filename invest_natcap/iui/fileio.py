import json
import ogr
from platform import node
import csv
import os

from dbfpy import dbf

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
        except IOError: #occurs if file not found
            self.dict = {}

    def get_attributes(self):
        if not self.dict:
            self._load_file()

        return self.dict

    def write_to_disk(self, dict):
        file = open(self.uri)
        file.writelines(json.dumps(dict))
        file.close()

class LastRunHandler(JSONHandler):
    def __init__(self, modelname):
        uri = './cfg' + modelname + '_lastrun_' + node() + '.json'
        JSONHandler.__init__(self, uri)

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
        self.update(uri)

    def update(self, uri):
        """Update the URI associated with this AbstractTableHandler object.

            uri - a python string target URI to be set as the new URI of this
                AbstractTableHandler.

            Returns nothing."""

        self.uri = uri
        self._get_field_names()
        self._get_table_list()

    def _open(self):
        """Function stub for reimplementation.

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

    def get_map(self, key_field, value_field):
        """Returns a python dictionary mapping values contained in key_field to
            values contained in value_field.  If duplicate keys are found, they
            are overwritten in the output dictionary.

            This is implemented as a dictionary comprehension on top of
            self.get_table_list(), so there shouldn't be a need to reimplement
            this for each subclass of AbstractTableHandler.

            If the table list has not been retrieved, it is retrieved before
            generating the map.

            returns a python dictionary mapping key_fields to value_fields."""

        if self.table == []:
            self._get_table_list()
        return dict((row[key_field], row[value_field]) for row in self.table)

class OGRHandler(AbstractTableHandler):
    def _open(self):
        self.file_obj = ogr.Open(str(self.uri))

    def _get_field_names(self):
        if self.file_obj != None:
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
    def _open(self):
        self.file_obj = dbf.Dbf(self.uri)

    def _get_field_names(self):
        dbf_file = self.file_object()
        self.orig_fieldnames = dict((name.lower(), name) for name in
            dbf_file.fieldNames)
        self.fieldnames = [r.lower() for r in dbf_file.fieldNames]

    def _get_table_list(self):
        db_file = self.open()
        table_list = []
        for record in db_file:
            record_dict = {}
            for fieldname in self.fieldnames:
                fieldname = fieldname.lower()
                record_dict[fieldname] = record[fieldname]
            table_list.append(record_dict)

        self.table = table_list

class CSVHandler(AbstractTableHandler):
    def _open(self):
        self.file_obj = csv.DictReader(open(self.uri))

    def _get_table_list(self):
        output_list = []
        for row in self.file_obj:
            output_list.append(row)

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

