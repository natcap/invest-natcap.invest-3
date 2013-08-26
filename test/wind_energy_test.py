import invest_natcap.testing

class WindEnergyRegressionTest(invest_natcap.testing.GISTest):
    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/wind_energy_regression_data/input_archive_val.tar.gz",
        workspace_archive="invest-data/test/data/wind_energy_regression_data/output_archive_val.tar.gz")
    def test_wind_energy_regression_val(self):
        invest_natcap.wind_energy.wind_energy.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/wind_energy_regression_data/input_archive_val_grid.tar.gz",
        workspace_archive="invest-data/test/data/wind_energy_regression_data/output_archive_val_grid.tar.gz")
    def test_wind_energy_regression_val_grid(self):
        invest_natcap.wind_energy.wind_energy.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/wind_energy_regression_data/input_archive_no_aoi.tar.gz",
        workspace_archive="invest-data/test/data/wind_energy_regression_data/output_archive_no_aoi.tar.gz")
    def test_wind_energy_regression_no_aoi(self):
        invest_natcap.wind_energy.wind_energy.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/wind_energy_regression_data/input_archive_suffix.tar.gz",
        workspace_archive="invest-data/test/data/wind_energy_regression_data/output_archive_suffix.tar.gz")
    def test_wind_energy_regression_suffix(self):
        invest_natcap.wind_energy.wind_energy.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/wind_energy_regression_data/input_archive_dist.tar.gz",
        workspace_archive="invest-data/test/data/wind_energy_regression_data/output_archive_dist.tar.gz")
    def test_wind_energy_regression_dist(self):
        invest_natcap.wind_energy.wind_energy.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/wind_energy_regression_data/input_archive_aoi_land.tar.gz",
        workspace_archive="invest-data/test/data/wind_energy_regression_data/output_archive_aoi_land.tar.gz")
    def test_wind_energy_regression_aoi_land(self):
        invest_natcap.wind_energy.wind_energy.execute(self.args)

    @invest_natcap.testing.regression(
        input_archive="invest-data/test/data/wind_energy_regression_data/input_archive_aoi.tar.gz",
        workspace_archive="invest-data/test/data/wind_energy_regression_data/output_archive_aoi.tar.gz")
    def test_wind_energy_regression_aoi(self):
        invest_natcap.wind_energy.wind_energy.execute(self.args)
