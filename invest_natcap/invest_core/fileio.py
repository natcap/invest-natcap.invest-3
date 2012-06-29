import csv

class TableDriverTemplate(object):
    """This class is merely a template to be subclassed for use with appropriate
    table filetype drivers.  Instantiating this object will yield a functional
    object, but it won't actually get you any relevant results."""

    def __init__(self, uri, fieldnames=None):
        """Constructor for the TableDriverTemplate object.  uri is a python
        string.  fieldnames is an optional list of python strings."""
        self.uri = uri

    def get_file_object(self, uri=None):
        """Return the library-specific file object by using the input uri.  If
        uri is None, return use self.uri."""
        return object

    def get_fieldnames(self):
        """Return a list of strings containing the fieldnames."""
        return []

    def write_table(self, table_list, uri=None, fieldnames=None):
        """Take the table_list input and write its contents to the appropriate
        URI.  If uri == None, write the file to self.uri.  Otherwise, write the
        table to uri (which may be a new file).  If fieldnames == None, assume
        that the default fieldnames order will be used."""
        pass

    def read_table(self):
        """Return the table object with data built from the table using the
        file-specific package as necessary.  Should return a list of
        dictionaries."""
        return [{}]


class CSVDriver(TableDriverTemplate):
    def get_file_object(self, uri=None):
        uri = max(uri, self.uri)
        return csv.DictReader(open(uri))

    def get_fieldnames(self):
        file_object = self.get_file_object(self.uri)
        if not hasattr(file_object, 'fieldnames'):
            fieldnames = file_object.next()
        else:
            fieldnames = file_object.fieldnames
        return fieldnames

    def read_table(self):
        file_object = self.get_file_object()
        table = []
        for row in file_object:
            table.append(row)  # row is a dictionary of values
        return table

    def write_table(self, table_list, uri=None, fieldnames=None):
        uri = max(uri, self.uri)
        fieldnames = max(fieldnames, self.get_fieldnames())
        writer = csv.DictWriter(open(uri), fieldnames)
        writer.writerows(table_list)

class DBFDriver(TableDriverTemplate):
    def get_file_object(self, uri=None):
        """Return the library-specific file object by using the input uri.  If
        uri is None, return use self.uri."""
        uri = max(uri, self.uri)
        return dbf.Dbf(uri, new=not os.path.exists(uri))

    def get_fieldnames(self):
        """Return a list of strings containing the fieldnames."""
        dbf_file = self.get_file_object(self.uri)
        return dbf_file.fieldNames

    def write_table(self, table_list, uri=None, fieldnames=None):
        """Take the table_list input and write its contents to the appropriate
        URI.  If uri == None, write the file to self.uri.  Otherwise, write the
        table to uri (which may be a new file).  If fieldnames == None, assume
        that the default fieldnames order will be used."""
        dbf_file = self.get_file_object(uri)
        fieldnames = max(fieldnames, self.get_fieldnames())

        # Check to see that all fieldnames exist already.  If a fieldname does
        # not exist, create it.
        fields_match = False
        while fields_match:
            for file_field, user_field in zip(dbf_file.header.fields, fieldnames):
                if file_field != user_field:
                    # Determine the appropriate field type to use
                    field_class = table_list[0][user_field].__class__.__name__
                    if class == 'int' or class == 'float':
                        new_field_def = ("N", 16, 6)
                    else:  # assume that this field is a string
                        new_field_def = ("C", 254, 0)
                    new_field_def = (user_field,) + new_field_def

                    # now that we've created a new field, we should start over
                    # to ensure that all fields align properly.
                    break
            # Once we can verify that all fields are the same, we can stop
            # checking fieldnames
            if dbf_file.header.fields == fieldnames:
                fields_match = True

        for index, row in zip(range(len(table_list)), table_list):
            for field in fieldnames:
                dbf_file[index][field] = row[field]

    def read_table(self):
        """Return the table object with data built from the table using the
        file-specific package as necessary.  Should return a list of
        dictionaries."""
        return [row.asDict() for row in self.get_file_object()]


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
