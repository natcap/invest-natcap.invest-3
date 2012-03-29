import json
import ogr
from platform import node
import csv

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

class TableHandler(object):
    def get_field_names(self, uri):
        """Function stub for reimplementation."""
        return []

class OGRHandler(TableHandler):
    def get_field_names(self, uri):
        """Get a list of the fieldnames in the specified OGR file.

            uri = a uri to an ogr DataSource

            returns a list of strings."""

        shapefile = ogr.Open(str(uri))
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

class DBFHandler(TableHandler):
    def get_field_names(self, uri):
        dbf_file = dbf.Dbf(str(uri))
        return dbf_file.header.fields

class CSVHandler(TableHandler):
    def open(self, uri):
        return csv.DictReader(open(uri))

    def get_field_names(self, uri):
        csv_file = self.open(uri)
        if not hasattr(csv_file, 'fieldnames'):
            return csv_file.next()
        else:
            return csv_file.fieldnames

    def get_map(self, uri, key_field, value_field):
        csv_file = self.open(uri)
        output_dict = {}
        for row in csv_file:
            output_dict[row[key_field]] = row[value_field]

        return output_dict
