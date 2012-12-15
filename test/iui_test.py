import unittest
import os.path

JSON_DIR = os.path.join('data', 'iui', 'sample_json')

class ContainerTest(unittest.TestCase):
    def setUp(self):
        container_test = os.path.join(JSON_DIR, 'test_container.json')

        # NEED TO FINISH THIS CALL!
        self.ui = base_widgets.ExecRoot()
