import csv

class TableDriverTemplate(object):
    """This class is merely a template to be subclassed for use with appropriate
    table filetype drivers.  Instantiating this object will yield a functional
    object, but it won't actually get you any relevant results."""

    def __init__(self, uri, fieldnames=None):
        """Constructor for the TableDriverTemplate object.  uri is a python
        string.  fieldnames is an optional list of python strings."""
        self.uri = uri
        self.file_obj = self.get_file_object(uri)

    def get_file_object(self, uri=None):
        """Return the library-specific file object by using the input uri.  If
        uri is None, return use self.uri."""
        return object

    def get_fieldnames(self):
        """Return a list of strings containing the fieldnames."""
        return []

    def write_table(self, table_list=[], uri=None):
        """Take the table_list input and write its contents to the appropriate
        URI.  If uri == None, write the file to self.uri.  Otherwise, write the
        table to uri (which may be a new file)."""
        pass

    def read_table(self):
        """Return the table object with data built from the table using the
        file-specific package as necessary.  Should return a list of
        dictionaries."""
        return [{}]


class CSVDriver(TableDriverTemplate):
    def get_file_object(self, uri):
        return csv.DictReader(open(uri))

    def get_fieldnames(self):
        if not hasattr(self.file_obj, 'fieldnames'):
            fieldnames = self.file_obj.next()
        else:
            fieldnames = self.file_obj.fieldnames

        self.fieldnames = [name.lower() for name in fieldnames]
        self.orig_fieldnames = dict((name.lower(), name) for name in
            fieldnames)





class TableHandler(object):
    def __init__(self, uri, fieldnames=None):
        """Constructor for the TableHandler class. uri is a python string.
        fieldnames, if not None, should be a python list of python strings."""
        self.driver = self.find_driver(uri, fieldnames)
        self.table = self.driver.read_table()
        self.fieldnames = self.driver.get_fieldnames()

    def __iter__(self):
        """Allow this handler object's table to be iterated through.  Returns an
        iterable version of self.table."""
        return iter(self.table)

    def write_table(self, table=None, uri=None):
        """Invoke the driver to save the table to disk.  If table == None,
        self.table will be written, otherwise, the list of dictionaries passed
        in to table will be written.  If uri is None, the table will be written
        to the table's original uri, otherwise, the table object will be written
        to uri."""
        if table == None:
            table = self.table
        self.driver.write_table(table, uri)
