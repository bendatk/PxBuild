import filecmp
from pathlib import Path

import pxbuild
from tests._paths import data_path, load_testdata_config


class TestCube2:
    def test_cube_2_ok(self, tmp_path):
        config = load_testdata_config(data_path("cubes", "cube_2", "test_config.json"), tmp_path)
        model = pxbuild.build_px_file("2", config)

        assert model.statistics.output_files
        path_expected = data_path("cubes", "cube_2", "expected")
        path_actual = Path(model.statistics.output_files[0]).parent
        for expected_file in path_expected.iterdir():
            result = filecmp.cmp(
                expected_file,
                path_actual / expected_file.name,
                shallow=False,
            )
            assert result, expected_file.name + " is not as expected."
