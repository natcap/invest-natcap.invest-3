"""Testing of recreation_server_core
"""
import unittest
import recreation_server_core


class PostgisTest(unittest.TestCase):
    """testing class"""

    def test_stats_box(self):
        """stats_box test
        """

        points = ((-1, 1), (1, -1), (0, 0))
        expected_results = (-1, -1, 1, 1, 2, 2)

        results = recreation_server_core.stats_box(points)

        self.assertEqual(results, expected_results)

    def test_bounding_box(self):
        """bounding_box test
        """

        points = ((-1, 1), (1, -1), (0, 0))
        expected_results = ((-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1))

        results = recreation_server_core.bounding_box(points)

        self.assertEqual(results, expected_results)

    def test_format_points_sql(self):
        """format_points_sql test
        """

        points = ((-1, 1), (1, -1), (0, 0))
        expected_results = "-1 1, 1 -1, 0 0"

        results = recreation_server_core.format_points_sql(points)

        self.assertEqual(results, expected_results)

    def test_format_polygon_sql(self):
        """format_polygon_sql test
        """

        points = ((-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1))
        srid = 4326
        expected_results = ("ST_GeomFromText(\'"
                            "POLYGON((-1 -1, -1 1, 1 1, 1 -1, -1 -1))\', 4326)")

        results = recreation_server_core.format_polygon_sql(points, srid)

        self.assertEqual(results, expected_results)

    def test_format_feature_sql(self):
        feature = "tag_value"
        expected_results = "osm.tag = \'value\'"

        results = recreation_server_core.format_feature_sql(feature)

        self.assertEqual(results, expected_results)

    def test_category_table(self):
        osm_table_name = "planet_osm_points"
        expected_results = "CREATE TABLE category_planet_osm_points (osm_id integer, cat smallint, PRIMARY KEY (osm_id))"

        results = recreation_server_core.category_table(osm_table_name)

        self.assertEqual(results, expected_results)


    def test_category_table_build(self):
        pass

    def category_dict(self):
        pass

    
        
if __name__ == '__main__':
    unittest.main()
