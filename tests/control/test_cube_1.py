import pxbuild
from tests._paths import data_path, load_testdata_config


class TestCube1:
    def test_cube_1_dont_crash(self, tmp_path):
        config = load_testdata_config(data_path("cubes", "cube_1", "test_config.json"), tmp_path)
        model = pxbuild.build_px_file("1", config)

        assert model.statistics.output_files
