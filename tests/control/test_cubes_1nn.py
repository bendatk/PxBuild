import filecmp
from pathlib import Path

import pxbuild
from tests._paths import data_path, load_testdata_config


class TestCubes1nn:
    # 101: missing row and value without symbol_columns
    # 102: missing row and value with 1 symbol_column
    # 103: missing row and value with 2 symbol_column
    # 104: as 103 but shuffled csv rows and cols
    # 130: as 103 but testing stupid columnnames in CSV
    # 131: as 103 but testing stupid columnnames in parquet

    def build(self, id: str, tmp_path) -> Path:
        config = load_testdata_config(data_path("cubes", "cubes_1nn", "config.json"), tmp_path)
        model = pxbuild.build_px_file(id, config)
        assert model.statistics.output_files
        return Path(model.statistics.output_files[0])

    def assert_expected_file(self, id: str, tmp_path) -> None:
        file = "tab_{id}.px".format(id=id)
        actual_path = self.build(id, tmp_path)
        result = filecmp.cmp(
            data_path("cubes", "cubes_1nn", "expected", file),
            actual_path,
            shallow=False,
        )
        assert result, file + " is not as expected."

    def test_cube_101_ok(self, tmp_path):
        self.assert_expected_file("101", tmp_path)

    def test_cube_102_ok(self, tmp_path):
        self.assert_expected_file("102", tmp_path)

    def test_cube_103_ok(self, tmp_path):
        self.assert_expected_file("103", tmp_path)

    def test_cube_104_ok(self, tmp_path):
        self.assert_expected_file("104", tmp_path)

    def test_cube_130_as_103_but_with_stupid_columnnames_csv(self, tmp_path):
        self.assert_expected_file("130", tmp_path)

    def test_cube_131_as_103_but_with_stupid_columnnames_parquet(self, tmp_path):
        self.assert_expected_file("131", tmp_path)
