
import invest_natcap.testing
import invest_natcap.marine_water_quality

class MarineWaterQualityRegressionTests(invest_natcap.testing.GISTest):
    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/marine_water_quality_regression/default_run_inputs.tar.gz",
        workspace_archive="invest-data/test/data/marine_water_quality_regression/default_run_outputs.tar.gz")
    def test_default_marine_water_quality_run(self):
        invest_natcap.marine_water_quality.marine_water_quality_biophysical.execute(self.args)

