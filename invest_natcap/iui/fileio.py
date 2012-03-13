import json
import ogr
from platform import node

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

class OGRHandler(object):
    def get_field_names(self, uri):
        """Get a list of the fieldnames in the specified OGR file.

            uri = a uri to an ogr DataSource

            returns a list of strings."""

        shapefile = ogr.Open(str(uri))
        layer = shapefile.GetLayer(0)
        layer_def = layer.GetLayerDefn()

        field_list = []
        for index in range(layer_def.GetFieldCount()):
            field_def = layer_def.GetFieldDefn(index)
            field_list.append(field_def.GetNameRef())

        return field_list



