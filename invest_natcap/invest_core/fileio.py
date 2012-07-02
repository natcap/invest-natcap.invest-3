import csv

class TableDriverTemplate(object):
    """ The TableDriverTemplate classes provide a uniform, simple way to
    interact with specific tabular libraries.  This allows us to interact with
    multiple filetypes in exactly the same way and in a uniform syntax.  By
    extension, this also allows us to read and write to and from any desired
    table format as long as the appropriate TableDriver class has been
    implemented.

    These driver classes exist for convenience, and though they can be accessed
    directly by the user, these classes provide only the most basic
    functionality.  Other classes, such as the TableHandler class, use these
    drivers to provide a convenient layer of functionality to the end-user.

    This class is merely a template to be subclassed for use with appropriate
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
    """The CSVDriver class is a subclass of TableDriverTemplate."""
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
    """The DBFDriver class is a subclass of TableDriverTemplate."""
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
                    if field_class == 'int' or field_class == 'float':
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

        # Now that we know all fields exist in this file, we can actually add
        # the record-specfic data to it.
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
        self.orig_fieldnames = {}
        self.mask = {'regexp': None,
                     'trim': 0}
        self.update(self.driver.uri)

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
        if uri == None:
            uri = self.uri
        self.driver.write_table(table, uri)

    def get_table(self):
        """Return the table list object."""
        return self.table

    def update(self, uri):
        """Update the URI associated with this AbstractTableHandler object.
            Updating the URI also rebuilds the fieldnames and internal
            representation of the table.

            uri - a python string target URI to be set as the new URI of this
                AbstractTableHandler.

            Returns nothing."""

        self.uri = uri
        self.driver = self.find_driver(uri, fieldnames=None)
        self.fieldnames = self.driver.get_fieldnames()

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

        self.mask['regexp'] = regexp
        self.mask['trim'] = trim
        if self.mask['regexp'] != None:
            map_to_trimmed_fields = dict((v, k[self.mask['trim']:]) if
                re.match(self.mask['regexp'], k) else (k, v) for (k, v) in
                self.orig_fielnames.iteritems())
            # If the user has set a mask for the fieldnames, create a dictionary
            # mapping the masked fieldnames to the original fieldnames and
            # create a new (masked) list of fieldnames according to the user's
            # mask.  Eventually, this will need to accommodate multiple forms of
            # masking ... maybe a function call inside of the comprehension?
            self.orig_fieldnames = dict((k[self.mask['trim']:], v) if
                re.match(self.mask['regexp'], k) else (k, v) for (k, v) in
                self.orig_fieldnames.iteritems())
            self.fieldnames = [f[self.mask['trim']:] if re.match(self.mask['regexp'],
                f) else f for f in self.fieldnames]

            # Regenerate the table list so we use the new mask
           # new_table = []
           # for row in self.table:
           #     new_row = {}
           #     for key, value in row.iteritems():
           #         new_row[map_to_trimmed_fields[key]] = value
           #     new_table.append(new_row)
           # self.table = new_table
            self.table = [dict((map_to_trimmed_fields[k], v) for (k,v) in
                row.iteritems()) for row in self.table]

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
