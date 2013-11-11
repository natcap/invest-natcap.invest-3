"""The invest_natcap.testing package defines core testing routines and
functionality."""

import csv
import filecmp
import functools
import glob
import hashlib
import json
import logging
import os
import shutil
import time
import unittest

import numpy
np = numpy
from osgeo import gdal
from osgeo import ogr


from invest_natcap.iui import executor
from invest_natcap.iui import fileio
from invest_natcap import raster_utils
import data_storage

LOGGER = logging.getLogger('invest_natcap.testing')

def get_hash(uri):
    """Get the MD5 hash for a single file.  The file is read in a
        memory-efficient fashion.

        uri - a string uri to the file to be tested.

        Returns a string hash for the file."""

    block_size = 2**20
    file_handler = open(uri)
    md5 = hashlib.md5()
    while True:
        data = file_handler.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def save_workspace(new_workspace):
    """Decorator to save a workspace to a new location."""

    # item is the function being decorated
    def test_inner_func(item):

        # this decorator indicates that this innermost function is wrapping up
        # the function passed in as item.
        @functools.wraps(item)
        def test_and_remove_workspace(self, *args, **kwargs):
            # This inner function actually executes the test function and then
            # moves the workspace to the folder passed in by the user.
            item(self)

            # remove the contents of the old folder
            try:
                shutil.rmtree(new_workspace)
            except OSError:
                pass

            # copy the workspace to the target folder
            old_workspace = self.workspace_dir
            shutil.copytree(old_workspace, new_workspace)
        return test_and_remove_workspace
    return test_inner_func


def regression(input_archive, workspace_archive):
    """Decorator to unzip input data, run the regression test and compare the
        outputs against the outputs on file.

        input_archive - the path to a .tar.gz archive with the input data.
        workspace_archive - the path to a .tar.gz archive with the workspace to
            assert.
         """

    # item is the function being decorated
    def test_inner_function(item):

        @functools.wraps(item)
        def test_and_assert_workspace(self, *args, **kwargs):
            workspace = raster_utils.temporary_folder()
            self.args = data_storage.extract_parameters_archive(workspace, input_archive)

            # Actually run the test.  Assumes that self.args is used as the
            # input arguments.
            item(self)

            # Extract the archived workspace to a new temporary folder and
            # compare the two workspaces.
            archived_workspace = raster_utils.temporary_folder()
            data_storage.extract_archive(archived_workspace, workspace_archive)
            self.assertWorkspace(workspace, archived_workspace)
        return test_and_assert_workspace
    return test_inner_function


def build_regression_archives(file_uri, input_archive_uri, output_archive_uri):
    file_handler = fileio.JSONHandler(file_uri)

    saved_data = file_handler.get_attributes()

    arguments = saved_data['arguments']
    model_id = saved_data['model']

    model_list = model_id.split('.')
    model = executor.locate_module(model_list)

    # guarantee that we're running this in a new workspace
    arguments['workspace_dir'] = raster_utils.temporary_folder()
    workspace = arguments['workspace_dir']

    # collect the parameters into a single folder
    input_archive = input_archive_uri
    if input_archive[-7:] == '.tar.gz':
        input_archive = input_archive[:-7]
    data_storage.collect_parameters(arguments, input_archive)
    input_archive += '.tar.gz'

    model_args = data_storage.extract_parameters_archive(workspace, input_archive)

    model.execute(model_args)

    archive_uri = output_archive_uri
    if archive_uri[-7:] == '.tar.gz':
        archive_uri = archive_uri[:-7]
    LOGGER.debug('Archiving the output workspace')
    shutil.make_archive(archive_uri, 'gztar', root_dir=workspace, logger=LOGGER)


class GISTest(unittest.TestCase):
    """A test class for our GIS testing functions."""

    def assertRastersEqual(self, a_uri, b_uri):
        """Tests if datasets a and b are 'almost equal' to each other on a per
            pixel basis

            aUri - a URI to a gdal dataset
            bUri - a URI to a  gdal dataset

            returns True if a and b are equal to each other"""

        LOGGER.debug('Asserting datasets A: %s, B: %s', a_uri, b_uri)

        for uri in [a_uri, b_uri]:
            if not os.path.exists(uri):
                raise IOError('File "%s" not found on disk' % uri)

        a_dataset = gdal.Open(a_uri)
        b_dataset = gdal.Open(b_uri)

        self.assertEqual(a_dataset.RasterXSize, b_dataset.RasterXSize,
            "x dimensions are different a=%s, second=%s" %
            (a_dataset.RasterXSize, b_dataset.RasterXSize))
        self.assertEqual(a_dataset.RasterYSize, b_dataset.RasterYSize,
            "y dimensions are different a=%s, second=%s" %
            (a_dataset.RasterYSize, b_dataset.RasterYSize))
        self.assertEqual(a_dataset.RasterCount, b_dataset.RasterCount,
            "different number of rasters a=%s, b=%s" % (
            (a_dataset.RasterCount, b_dataset.RasterCount)))

        for band_number in range(1, a_dataset.RasterCount + 1):
            band_a = a_dataset.GetRasterBand(band_number)
            band_b = b_dataset.GetRasterBand(band_number)

            a_array = band_a.ReadAsArray(0, 0, band_a.XSize, band_a.YSize)
            b_array = band_b.ReadAsArray(0, 0, band_b.XSize, band_b.YSize)

            try:
                numpy.testing.assert_array_almost_equal(a_array, b_array)
            except AssertionError:
                for row_index in xrange(band_a.YSize):
                    for pixel_a, pixel_b in zip(a_array[row_index], b_array[row_index]):
                        self.assertAlmostEqual(pixel_a, pixel_b,
                            msg='%s != %s ... Failed at row %s' %
                            (pixel_a, pixel_b, row_index))

    def assertVectorsEqual(self, aUri, bUri):
        """Tests if shapes a and b are equal to each other on a
           layer, feature, and field basis

           aUri - a URI to a ogr shapefile
           bUri - a URI to a ogr shapefile

           returns True if a and b are equal to each other"""

        for uri in [aUri, bUri]:
            if not os.path.exists(uri):
                raise IOError('File "%s" not found on disk' % uri)

        shape = ogr.Open(aUri)
        shape_regression = ogr.Open(bUri)

        # Check that the shapefiles have the same number of layers
        layer_count = shape.GetLayerCount()
        layer_count_regression = shape_regression.GetLayerCount()
        self.assertEqual(layer_count, layer_count_regression,
                         'The shapes DO NOT have the same number of layers')

        for layer_num in range(layer_count):
            # Get the current layer
            layer = shape.GetLayer(layer_num)
            layer_regression = shape_regression.GetLayer(layer_num)
            # Check that each layer has the same number of features
            feat_count = layer.GetFeatureCount()
            feat_count_regression = layer_regression.GetFeatureCount()
            self.assertEqual(feat_count, feat_count_regression,
                             'The layers DO NOT have the same number of features')

            self.assertEqual(layer.GetGeomType(), layer_regression.GetGeomType(),
                'The layers do not have the same geometry type')


            # Get the first features of the layers and loop through all the features
            feat = layer.GetNextFeature()
            feat_regression = layer_regression.GetNextFeature()
            while feat is not None:
                # Check that the field counts for the features are the same
                layer_def = layer.GetLayerDefn()
                layer_def_regression = layer_regression.GetLayerDefn()
                field_count = layer_def.GetFieldCount()
                field_count_regression = layer_def_regression.GetFieldCount()
                self.assertEqual(field_count, field_count_regression,
                                 'The shapes DO NOT have the same number of fields')

                for fld_index in range(field_count):
                    # Check that the features have the same field values
                    field = feat.GetField(fld_index)
                    field_regression = feat_regression.GetField(fld_index)
                    self.assertEqual(field, field_regression,
                                         'The field values DO NOT match')
                    # Check that the features have the same field name
                    field_ref = feat.GetFieldDefnRef(fld_index)
                    field_ref_regression = \
                        feat_regression.GetFieldDefnRef(fld_index)
                    field_name = field_ref.GetNameRef()
                    field_name_regression = field_ref_regression.GetNameRef()
                    self.assertEqual(field_name, field_name_regression,
                                         'The fields DO NOT have the same name')
                # Check that the features have the same geometry
                geom = feat.GetGeometryRef()
                geom_regression = feat_regression.GetGeometryRef()

                self.assertTrue(geom.Equals(geom_regression))

                if layer.GetGeomType() != ogr.wkbPoint:
                    # Check that the features have the same area,
                    # but only if the shapefile's geometry is not a point, since
                    # points don't have area to check.
                    self.assertEqual(geom.Area(), geom_regression.Area())

                feat = None
                feat_regression = None
                feat = layer.GetNextFeature()
                feat_regression = layer_regression.GetNextFeature()

        shape = None
        shape_regression = None

    def assertCSVEqual(self, aUri, bUri):
        """Tests if csv files a and b are 'almost equal' to each other on a per
            cell basis

            aUri - a URI to a csv file
            bUri - a URI to a csv file

            returns True if a and b are equal to each other"""

        a = open(aUri)
        b = open(bUri)

        reader_a = csv.reader(a)
        reader_b = csv.reader(b)

        for index, (a_row, b_row) in enumerate(zip(reader_a, reader_b)):
            try:
                self.assertEqual(a_row, b_row,
                    'Rows differ at row %s: a=%s b=%s' % (index, a_row, b_row))
            except AssertionError:
                for col_index, (a_element, b_element) in enumerate(zip(a_row, b_row)):
                    try:
                        a_element = float(a_element)
                        b_element = float(b_element)
                        self.assertAlmostEqual(a_element, b_element,
                            msg=('Values are significantly different at row %s col %s:'
                             ' a=%s b=%s' % (index, col_index, a_element,
                             b_element)))
                    except ValueError:
                        # we know for sure they arenot floats, so compare as
                        # non-floats.
                        self.assertEqual(a_element, b_element,
                            msg=('Elements differ at row %s col%s: a=%s b=%s' %
                            (index, col_index, a_element, b_element)))

    def assertMD5(self, uri, regression_hash):
        """Tests if the input file has the same hash as the regression hash
            provided.

            uri - a string URI to the file to be tested.
            regression_hash - a string hash to be tested."""

        self.assertEqual(get_hash(uri), regression_hash, "MD5 Hashes differ.")

    def assertArchives(self, archive_1_uri, archive_2_uri):
        """Unzip the two archives and compare its contents.  Archives must be
            tar.gz."""

        archive_1_folder = raster_utils.temporary_folder()
        data_storage.extract_archive(archive_1_folder, archive_1_uri)

        archive_2_folder = raster_utils.temporary_folder()
        data_storage.extract_archive(archive_2_folder, archive_2_uri)

        self.assertWorkspace(archive_1_folder, archive_2_folder)

    def assertWorkspace(self, archive_1_folder, archive_2_folder,
            glob_exclude=''):
        """Check the contents of two folders against each other.

        archive_1_folder - a uri to a folder on disk
        archive_2_folder - a uri to a folder on disk
        glob_exclude='' - a string in glob format representing files to ignore"""

        # uncompress the two archives

        archive_1_files = []
        archive_2_files = []
        for files_list, workspace in [
                (archive_1_files, archive_1_folder),
                (archive_2_files, archive_2_folder)]:
            for root, dirs, files in os.walk(workspace):
                root = root.replace(workspace + os.sep, '')
                ignored_files = glob.glob(glob_exclude)
                for filename in files:
                    if filename not in ignored_files:
                        full_path = os.path.join(root, filename)
                        files_list.append(full_path)

        archive_1_files = sorted(archive_1_files)
        archive_2_files = sorted(archive_2_files)

        archive_1_size = len(archive_1_files)
        archive_2_size = len(archive_2_files)
        if archive_1_size != archive_2_size:
            # find out which archive had more files.
            archive_1_files = map(lambda x: x.replace(archive_1_folder, ''),
                archive_1_files)
            archive_2_files = map(lambda x: x.replace(archive_2_folder, ''),
                archive_2_files)
            missing_from_archive_1 = list(set(archive_2_files) -
                set(archive_1_files))
            missing_from_archive_2 = list(set(archive_1_files) -
                set(archive_2_files))
            raise AssertionError('Elements missing from A:%s, from B:%s' %
                (missing_from_archive_1, missing_from_archive_2))
        else:
            # archives have the same number of files that we care about
            for file_1, file_2 in zip(archive_1_files, archive_2_files):
                file_1_uri = os.path.join(archive_1_folder, file_1)
                file_2_uri = os.path.join(archive_2_folder, file_2)
                LOGGER.debug('Checking %s, %s', file_1, file_2)
                self.assertFiles(file_1_uri, file_2_uri)

    def assertJSON(self, json_1_uri, json_2_uri):
        """Assert two JSON objects against each other.

            json_1_uri - a uri to a JSON object in a file.
            json_2_uri - a uri to a JSON object in a file."""

        dict_1 = json.loads(open(json_1_uri).read())
        dict_2 = json.loads(open(json_2_uri).read())

        self.maxDiff = None
        self.assertEqual(dict_1, dict_2)

    def assertTextEqual(self, text_1_uri, text_2_uri):
        """Assert that two text files are equal.  This is done by looping
        through each line in the text files and asserting that each line matches
        the other.  If a mismatch occurs, an AssertionError will be raised.

        text_1_uri - a python string uri to a text file.  Considered the file to
            be tested.
        text_2_uri - a python string uri to a text file.  Considered the
            regression file."""

        lines = lambda f: [line for line in open(f)]
        for index, (a_line, b_line) in enumerate(zip(lines(text_1_uri), lines(text_2_uri))):
            self.assertEqual(a_line, b_line, ('Line %s in %s does not match'
                'regression file. Output: \"%s\" Regression: \"%s\"') % (index,
                text_1_uri, a_line, b_line))

    def assertFiles(self, file_1_uri, file_2_uri):
        """Assert two files are equal.  We try to determine the filetype based
        on the input URI extensions (which are assumed to be the same). If we do
        not recognize the filetypes, check the file's MD5sum."""

        for uri in [file_1_uri, file_2_uri]:
            self.assertEqual(os.path.exists(uri), True,
                'File %s does not exist' % uri)

        # assert the extensions are the same
        file_1_ext = os.path.splitext(file_1_uri)[1]
        file_2_ext = os.path.splitext(file_2_uri)[1]
        self.assertEqual(file_1_ext, file_2_ext, 'Extensions differ: %s, %s' %
            (file_1_ext, file_2_ext))

        assert_funcs = {
            '.json': self.assertJSON,
            '.tif': self.assertRastersEqual,
            '.shp': self.assertVectorsEqual,
            '.csv': self.assertCSVEqual,
            '.txt': self.assertTextEqual,
            '.html': self.assertTextEqual,
        }

        try:
            assert_funcs[file_1_ext](file_1_uri, file_2_uri)
        except KeyError:
            # When we're given an extension we don't have a function for, assert
            # the MD5s.
            file_1_md5 = get_hash(file_1_uri)
            file_2_md5 = get_hash(file_2_uri)
            self.assertEqual(file_1_md5, file_2_md5,
                'Files %s and %s differ (MD5sum)' % (file_1_uri, file_2_uri))

