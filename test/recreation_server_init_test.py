"""Testing of recreation_server_core
"""
import unittest
import recreation_server_init


class RecreationServerInitTest(unittest.TestCase):
    """testing class"""

    def test_bc(self):
        config_file_name = "recreation_server_config.json"
        config_file_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        config_file_path = os.path.join(config_file_path, config_file_name)
        config_file = open(config_file_path, 'r')
        config = json.loads(config_file.read())
        config_file.close()

        model = {"sessid": "unittest",
                 "grid_type": "1",
                 "cell_size": 10000.0,
                 "user_predictors": 2,
                 "user_tables": 0,
                 "download": true,
                 "landscan": false,
                 "osm_point": false,
                 "osm_line": false,
                 "osm_poly": false,                 
                 "protected": false,
                 "mangroves": false,
                 "lulc": false,
                 "reefs": false,
                 "grass": false}        

if __name__ == '__main__':
    unittest.main()
