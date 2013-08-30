import invest_natcap.testing
import invest_natcap.hydropower.hydropower_water_yield

class HydropowerRegressionTest(invest_natcap.testing.GISTest):
    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/hydropower_regression_data/hydro_input_archive_valuation.tar.gz",
        workspace_archive="invest-data/test/data/hydropower_regression_data/hydro_output_archive_valuation.tar.gz")
    def test_hydropower_regression_test_valuation(self):
        invest_natcap.hydropower.hydropower_water_yield.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/hydropower_regression_data/hydro_input_archive_scarcity.tar.gz",
        workspace_archive="invest-data/test/data/hydropower_regression_data/hydro_output_archive_scarcity.tar.gz")
    def test_hydropower_regression_test_scarcity(self):
        invest_natcap.hydropower.hydropower_water_yield.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/hydropower_regression_data/hydro_input_archive_wy_sub_sheds.tar.gz",
        workspace_archive="invest-data/test/data/hydropower_regression_data/hydro_output_archive_wy_sub_sheds.tar.gz")
    def test_hydropower_regression_test_wy_sub_sheds(self):
        invest_natcap.hydropower.hydropower_water_yield.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/hydropower_regression_data/hydro_input_archive_water_yield.tar.gz",
        workspace_archive="invest-data/test/data/hydropower_regression_data/hydro_output_archive_water_yield.tar.gz")
    def test_hydropower_regression_test_water_yield(self):
        invest_natcap.hydropower.hydropower_water_yield.execute(self.args)

