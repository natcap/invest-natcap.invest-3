"""Unit Tests For Reporting Package"""

import os, sys
from osgeo import gdal
from osgeo import ogr
import unittest
from nose.plugins.skip import SkipTest
import invest_natcap.testing as testing

#from invest_natcap import reporting
import invest_natcap.reporting as reporting
from invest_natcap.reporting import table_generator
import invest_test_core

REPORTING_DATA = os.path.join('invest-data/test/data', 'reporting_data')

STYLE_DATA = os.path.join('invest-data/test/data', 'style_data')
REGRESSION_DATA = os.path.join(
    'invest-data/test/data', 'reporting_data', 'regression_data')
TEST_OUT = os.path.join('invest-data/test/data', 'test_out')

class TestReportingPackage(testing.GISTest):
    def test_generate_html_smoke(self):
        """Regression test for creating a html report with no elements passed
            in. Expecting a blank html page created."""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_smoke.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_smoke.html')

        report_args = {
                'title': 'Test Title',
                'elements': [],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html(self):
        """Regression test for creating a html report with a table element
            from a dictionary and an external css file"""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_dict.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_dict.html')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')

        sample_dict = [{'date':'9/13', 'price':'expensive', 'product':'chips'},
                        {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                        {'date':'5/12', 'price':'moderate', 'product':'mints'}]

        columns = [
                {'name': 'date', 'total':False},
                {'name': 'price', 'total':False},
                {'name': 'product', 'total':False}]

        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
                        'checkbox': False,
                        'total': False,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'src': css_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_csv(self):
        """Regression test for creating a html report with a table element
            from a CSV file and an external css file"""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_csv.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_csv.html')
        csv_uri = os.path.join(REPORTING_DATA, 'csv_test.csv')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')

        columns = [{'name': 'ws_id', 'total':False},
                    {'name': 'precip_mn', 'total':False},
                    {'name': 'wyield_mn', 'total':False},
                    {'name': 'wyield_vol', 'total':True}]

        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
                        'checkbox': False,
                        'total': False,
                        'data_type':'csv',
                        'columns':columns,
                        'key':'ws_id',
                        'data': csv_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'src': css_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_shape(self):
        """Regression test for creating a html report with a table element
            from a shapefile and an external css file"""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_shp.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_shp.html')
        shape_uri = os.path.join(REPORTING_DATA, 'shape_test.shp')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')

        columns = [{'name': 'ws_id', 'total':False},
                    {'name': 'precip_mn', 'total':False},
                    {'name': 'wyield_mn', 'total':False},
                    {'name': 'wyield_vol', 'total':True}]

        report_args = {
                'title': 'Test Title',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': False,
                        'checkbox': False,
                        'total': False,
                        'data_type':'shapefile',
                        'columns':columns,
                        'key':'ws_id',
                        'data': shape_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'src': css_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_robust(self):
        """Regression test for making a robust html page. Pass in a table
            element from a dictionary, css style, and javascript source.
            This table should be sortable"""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_sorttable.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_sortable.html')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')
        jsc_uri = os.path.join(REPORTING_DATA,'sorttable.js')

        sample_dict = [{'date':'9/13', 'price':'expensive', 'product':'chips'},
                       {'date':'3/13', 'price':'cheap', 'product':'peanuts'},
                       {'date':'5/12', 'price':'moderate', 'product':'mints'}]

        columns = [{'name': 'date', 'total':False},
                   {'name': 'price', 'total':False},
                   {'name': 'product', 'total':True}]

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'text',
                        'section': 'body',
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': False,
                        'total': False,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'src': css_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'src': jsc_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_add_head_element_link(self):
        """Unit test for adding link head elements to html file"""
        raise SkipTest
        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'reporting_add_head_element.html')
        example_style_uri = os.path.join(REPORTING_DATA, 'table_style.css')

        args = {'format':'link', 'src':example_style_uri, 'out_uri':output_uri}

        expected_result = \
                '<link rel=stylesheet type=text/css href=./table_style.css>'

        result = reporting.add_head_element(args)

        self.assertEqual(expected_result, result)

        os.remove(os.path.join(TEST_OUT, 'table_style.css'))

    def test_add_head_element_script(self):
        """Unit test for adding script head elements to html file"""
        raise SkipTest
        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'reporting_add_head_element.html')
        example_script_uri = os.path.join(REPORTING_DATA, 'sorttable.js')

        args = {'format':'script', 'src':example_script_uri,
                'out_uri':output_uri}

        expected_result = \
                '<script type=text/javascript src=./sorttable.js></script>'

        result = reporting.add_head_element(args)

        self.assertEqual(expected_result, result)

        os.remove(os.path.join(TEST_OUT, 'sorttable.js'))

    def test_add_head_element_script_exception(self):
        """Unit test for adding script head elements to html file with a faulty
            script URI. Should raise an IOError with a nice message"""
        raise SkipTest
        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'reporting_add_head_element.html')
        example_script_uri = os.path.join(REPORTING_DATA, 'foo_bar.js')

        args = {'format':'script', 'src':example_script_uri,
                'out_uri':output_uri}

        self.assertRaises(IOError, reporting.add_head_element, (args))

    def test_generate_html_checkbox(self):
        """Regression test for making a robust html page. Pass in a table
            element from a dictionary, css style, javascript source,
            and enable checkbox column. This table should be sortable
            with a checkbox column that does selected totals"""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_checkbox.html')
        reg_uri = os.path.join(REGRESSION_DATA, 'regres_html_test_checkbox.html')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')
        jsc_uri = os.path.join(REPORTING_DATA,'sorttable.js')
        jquery_uri = os.path.join(REPORTING_DATA,'jquery-1.10.2.min.js')
        jsc_fun_uri = os.path.join(REPORTING_DATA,'total_functions.js')

        sample_dict = [{'date':'9/13', 'price':100, 'product':'chips'},
                       {'date':'3/13', 'price':25, 'product':'peanuts'},
                       {'date':'5/12', 'price':60, 'product':'mints'}]

        columns = [{'name': 'date', 'total':False},
                   {'name': 'price', 'total':True},
                   {'name': 'product', 'total':False}]

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'text',
                        'section': 'body',
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total': False,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'src': css_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'src': jsc_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'src': jquery_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'src': jsc_fun_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_javascript_totals(self):
        """Regression test for making a robust html page. Pass in a table
            element from a dictionary, css style, javascript source,
            and enable checkbox column as well as constant totals.
            This table should be sortable with a checkbox column that
            does selected totals"""

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_javascript_totals.html')
        reg_uri = os.path.join(
                REGRESSION_DATA, 'regres_html_test_javascript_totals.html')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')
        jsc_uri = os.path.join(REPORTING_DATA,'sorttable.js')
        jquery_uri = os.path.join(REPORTING_DATA,'jquery-1.10.2.min.js')
        jsc_fun_uri = os.path.join(REPORTING_DATA,'total_functions.js')

        sample_dict = [{'date':'13', 'price':'1', 'product':'chips'},
                       {'date':'3', 'price':'2', 'product':'peanuts'},
                       {'date':'5', 'price':'3', 'product':'mints'}]

        columns = [{'name': 'date', 'total':False},
                   {'name': 'price', 'total':True},
                   {'name': 'product', 'total':False}]

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'text',
                        'section': 'body',
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total':True,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'link',
                        'src': css_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'src': jsc_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'src': jquery_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'src': jsc_fun_uri}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_multiple_tables(self):
        """Regression test for making a html page with multiple tables.
        """

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_multi_tables_list.html')
        reg_uri = os.path.join(
                REGRESSION_DATA, 'regres_html_test_multi_tables.html')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')
        jsc_uri = os.path.join(REPORTING_DATA,'sorttable.js')
        jquery_uri = os.path.join(REPORTING_DATA,'jquery-1.10.2.min.js')
        #jsc_fun_uri = os.path.join(REPORTING_DATA,'total_functions.js')
        csv_uri = os.path.join(REPORTING_DATA, 'csv_test.csv')

        js_string = '''
            $(document).ready(function()
                    {
                        sum_constant_total();
                    });

            $(function(){

                $('[name="cb"]').change(function() {

                    $table = $(this).closest('table');

                    //$('.checkTot').html("0");
                    $table.find('.checkTot').html("0");
                    //$('[name="cb"]:checked').closest('tr').find('.rowDataSd').each(function() {
                    $table.find('[name="cb"]:checked').closest('tr').find('.rowDataSd').each(function() {
                        var $td = $(this);
                        //var $sumColumn = $(this).find('tr.checkTotal td:eq(' + $td.index() + ')');
                        var $sumColumn = $table.find('tr.checkTotal td:eq(' + $td.index() + ')');
                        var currVal = $sumColumn.html() || 0;
                        currVal = +currVal + +$td.html();
                        $sumColumn.html(currVal);
                        });

                    });
            });

            function sum_constant_total() {

                $('table').each(function(){

                    var totals_array = new Array();

                    //var $dataRows=$("#my_table tr:not('.totalColumn')");
                    var $dataRows=$(this).find("tr:not('.totalColumn')");

                    $dataRows.each(function() {
                        $(this).find('.rowDataSd').each(function(i){
                            totals_array[i] = 0;
                        });
                    });

                    $dataRows.each(function() {
                        $(this).find('.rowDataSd').each(function(i){
                            totals_array[i]+=parseFloat( $(this).html());
                        });
                    });

                    //$("#my_table td.totalCol").each(function(i){
                    $(this).find("td.totalCol").each(function(i){
                        $(this).html(totals_array[i]);
                    });
                });
            }'''

        #sample_dict = [{'date':'13', 'price':'1.5', 'product':'chips'},
        #               {'date':'3', 'price':'2.25', 'product':'peanuts'},
        #               {'date':'5', 'price':'3.2', 'product':'mints'}]

        sample_dict = []

        columns = [{'name': 'product', 'total':False},
                   {'name': 'date', 'total':False},
                   {'name': 'price', 'total':True}]

        columns_csv = [
                {'name': 'ws_id', 'total':False},
                {'name': 'precip_mn', 'total':True},
                {'name': 'wyield_mn', 'total':False},
                {'name': 'wyield_vol', 'total':True}]

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': False,
                        'total':False,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'ws_id',
                        'data': sample_dict},
                    {
                        'type': 'text',
                        'section': 'body',
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total':True,
                        'data_type':'csv',
                        'columns':columns_csv,
                        'key':'ws_id',
                        'data': csv_uri},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'style',
                        'data_src': css_uri,
                        'input_type': 'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': jsc_uri,
                        'input_type': 'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': jquery_uri,
                        'input_type': 'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': js_string,
                        'input_type': 'Text'}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_interactive_tables(self):
        """Regression test for making a html page where two tables
            talk to each other.
        """

        raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_interactive_tables_list.html')
        reg_uri = os.path.join(
                REGRESSION_DATA, 'regres_html_test_multi_tables.html')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')
        jsc_uri = os.path.join(REPORTING_DATA,'sorttable.js')
        jquery_uri = os.path.join(REPORTING_DATA,'jquery-1.10.2.min.js')
        jsc_fun_uri = os.path.join(REPORTING_DATA,'permitting_functions.js')
        json_uri = os.path.join(REPORTING_DATA,'sample_json.json')
        csv_uri = os.path.join(REPORTING_DATA, 'csv_test.csv')

        sample_dict = [{'Sediment':'130', 'Nitrogen':'90', 'Phosphorous':'60', 'parcel_id':'1'},
                       {'Sediment':'96', 'Nitrogen':'50', 'Phosphorous':'60','parcel_id':'2'},
                       {'Sediment':'36', 'Nitrogen':'110', 'Phosphorous':'60','parcel_id':'3'},
                       {'Sediment':'50', 'Nitrogen':'85', 'Phosphorous':'60','parcel_id':'4'}]

        columns = [{'name': 'parcel_id', 'total':False},
                   {'name': 'Nitrogen', 'total':True},
                   {'name': 'Sediment', 'total':True},
                   {'name': 'Phosphorous', 'total':True}]

        pop_groups = []

        columns_pop = [
                {'name': 'municipalities', 'total':False},
                {'name': 'Sediment', 'total':False},
                {'name': 'Nitrogen', 'total':False},
                {'name': 'Phosphorous', 'total':False}]

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total':True,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'parcel_id',
                        'data': sample_dict},
                    {
                        'type': 'text',
                        'section': 'body',
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': False,
                        'total':False,
                        'data_type':'dictionary',
                        'columns':columns_pop,
                        'key':'pop_group',
                        'data': pop_groups},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'style',
                        'data_src': css_uri,
                        'input_type':'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': jsc_uri,
                        'input_type':'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': jquery_uri,
                        'input_type':'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': jsc_fun_uri,
                        'input_type':'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'json',
                        'data_src': json_uri,
                        'input_type':'File'}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)

    def test_generate_html_svg(self):
        """Regression test for making a html page with embedded svg.
        """

        #raise SkipTest

        if not os.path.isdir(TEST_OUT):
            os.makedirs(TEST_OUT)

        output_uri = os.path.join(TEST_OUT, 'html_test_svg.html')
        reg_uri = os.path.join(
                REGRESSION_DATA, 'regres_html_test_multi_tables.html')
        css_uri = os.path.join(REPORTING_DATA,'table_style.css')
        svg_css_uri = os.path.join(STYLE_DATA,'test_css.css')
        svg_out_uri = os.path.join(TEST_OUT, 'svg_test_out.svg')
        shape_uri = os.path.join(STYLE_DATA, 'subwatersheds.shp')

        jsc_uri = os.path.join(REPORTING_DATA,'sorttable.js')
        jquery_uri = os.path.join(REPORTING_DATA,'jquery-1.10.2.min.js')
        jsc_fun_uri = os.path.join(REPORTING_DATA,'permitting_functions.js')
        json_uri = os.path.join(REPORTING_DATA,'sample_json.json')
        csv_uri = os.path.join(REPORTING_DATA, 'csv_test.csv')

        sample_dict = [{'Sediment':'130', 'Nitrogen':'90', 'Phosphorous':'60', 'parcel_id':'1'},
                       {'Sediment':'96', 'Nitrogen':'50', 'Phosphorous':'60','parcel_id':'2'},
                       {'Sediment':'36', 'Nitrogen':'110', 'Phosphorous':'60','parcel_id':'3'},
                       {'Sediment':'50', 'Nitrogen':'85', 'Phosphorous':'60','parcel_id':'4'}]

        columns = [{'name': 'parcel_id', 'total':False},
                   {'name': 'Nitrogen', 'total':True},
                   {'name': 'Sediment', 'total':True},
                   {'name': 'Phosphorous', 'total':True}]

        pop_groups = []

        columns_pop = [
                {'name': 'municipalities', 'total':False},
                {'name': 'Sediment', 'total':False},
                {'name': 'Nitrogen', 'total':False},
                {'name': 'Phosphorous', 'total':False}]

        report_args = {
                'title': 'Sortable Table',
                'elements': [
                    {
                        'type': 'svg',
                        'section': 'body',
                        'svg_out_uri': svg_out_uri,
                        'source_uri': shape_uri,
                        'field_id': 'subws_id',
                        'key_id': 'subws_id',
                        'proj_type': 'mercator',
                        'css_uri': svg_css_uri,
                        'size': (400, 600)},
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': True,
                        'total':True,
                        'data_type':'dictionary',
                        'columns':columns,
                        'key':'parcel_id',
                        'data': sample_dict},
                    {
                        'type': 'text',
                        'section': 'body',
                        'text': '<p>Here is a sortable table!</p>'},
                    {
                        'type': 'table',
                        'section': 'body',
                        'sortable': True,
                        'checkbox': False,
                        'total':False,
                        'data_type':'dictionary',
                        'columns':columns_pop,
                        'key':'pop_group',
                        'data': pop_groups},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'style',
                        'data_src': css_uri,
                        'input_type':'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': jsc_uri,
                        'input_type':'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': jquery_uri,
                        'input_type':'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'script',
                        'data_src': jsc_fun_uri,
                        'input_type':'File'},
                    {
                        'type': 'head',
                        'section': 'head',
                        'format': 'json',
                        'data_src': json_uri,
                        'input_type':'File'}
                    ],
                'out_uri': output_uri}

        reporting.generate_report(report_args)

        self.assertFiles(output_uri, reg_uri)
