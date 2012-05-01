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
    def __init__(self, uri):
        self.uri = uri

    def open(self):
        pass

    def get_field_names(self):
        pass

    def get_table_list(self):
        pass

    def get_map(self):
        pass

class OGRHandler(AbstractTableHandler):
    def open(self):
        return ogr.Open(self.uri)

    def get_field_names(self):
        """Get a list of the fieldnames in the specified OGR file.

            uri = a uri to an ogr DataSource

            returns a list of strings."""

        shapefile = ogr.Open(str(self.uri))
        if shapefile != None:
            layer = shapefile.GetLayer(0)
            layer_def = layer.GetLayerDefn()

            field_list = []
            for index in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(index)
                field_list.append(field_def.GetNameRef())

            return field_list
        else:
            return []

class DBFHandler(AbstractTableHandler):
    def open(self):
        return dbf.Dbf(self.uri)

    def get_field_names(self):
        dbf_file = dbf.Dbf(str(self.uri))
        return dbf_file.header.fields

class CSVHandler(AbstractTableHandler):
    def open(self):
        return csv.DictReader(open(self.uri))

    def get_table_list(self):
        reader = self.open(self.uri)
        output_list = []
        for row in reader:
            output_list.append(row)

        return output_list

    def get_field_names(self):
        csv_file = self.open(self.uri)
        if not hasattr(csv_file, 'fieldnames'):
            return csv_file.next()
        else:
            return csv_file.fieldnames

    def get_map(self, uri, key_field, value_field):
        csv_file = self.open(self.uri)
        output_dict = {}
        for row in csv_file:
            output_dict[row[key_field]] = row[value_field]

        return output_dict


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
        open_file = handler.open()
        if open_file == None: raise InvalidExtension

    except KeyError, InvalidExtension:
        print ext.lower()
        # if for some reason, the defined filetype doesn't exist in the
        # filetypes dictionary, loop through all of the available handlers
        for class_reference in FILETYPES.values():
            handler = class_reference(uri)
            opened_file = handler.open(uri)
            if opened_file != None: break

    return handler

