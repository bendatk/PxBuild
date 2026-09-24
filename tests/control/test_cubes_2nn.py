import filecmp
from pathlib import Path

import pxbuild
from tests._paths import data_path, load_testdata_config


class TestCubes2nn:
    # 200: many notes and metaid

    def test_cube_200_ok(self, tmp_path):
        config = load_testdata_config(data_path("cubes", "cubes_2nn", "config.json"), tmp_path)
        model = pxbuild.build_px_file("200", config)

        assert model.statistics.output_files
        file = "tab_200.px"
        result = filecmp.cmp(
            data_path("cubes", "cubes_2nn", "expected", file),
            Path(model.statistics.output_files[0]),
            shallow=False,
        )
        assert result, file + " is not as expected."
