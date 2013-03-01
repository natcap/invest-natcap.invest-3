import unittest

from invest_natcap.aesthetic_quality import aesthetic_quality


class AestheticQualityTest(unittest.TestCase):
    """Test class for test functions of the AQ model"""

    def test_smoke(self):
        """Smoke test for aq"""

        args = {}
        args['workspace_dir'] = 'data/test_out/aq_workspace'
        args['aoiFileName'] = ''
        args['structureFileName'] = ''
        args['structureFileName'] = ''
        args['refraction'] = 0.13
        args['cellSize'] = 30
        args['populationFileName'] = ''
        args['overlapFileName'] = ''
        aesthetic_quality.execute(args)
