import pxbuild


def _data_section(path: str) -> str:
    """Return the DATA=... payload of a .px file, ignoring everything before it.

    Only the DATA section is compared across these tests: the surrounding
    metadata (TABLEID, TITLE, MATRIX, CONTENTS, ...) intentionally differs
    between the test cubes, only the numeric data matters here.
    """
    with open(path, encoding="iso-8859-1") as fh:
        content = fh.read()
    return content.split("DATA=", 1)[1]


class TestCubes1nn:
    # 101: missing row and value without symbol_columns
    # 102: missing row and value with 1 symbol_column
    # 103: missing row and value with 2 symbol_column
    # 104: as 103 but shuffled csv rows and cols
    # 130: as 103 but testing stupid columnnames in CSV
    # 131: as 103 but testing stupid columnnames in parquet

    def set_path(self) -> None:
        # pytest dont like dunder init
        self._my_path = "testdata/test_cubes_1nn/"
        self._my_config = self._my_path + "config.json"

    def get_actual_path(self, id: str) -> str:
        return "testdata/out_files/cubes_1nn/test_cube_{id}/".format(id=id)

    def build(self, id: str) -> str:
        self.set_path()
        model = pxbuild.build_px_file(id, self._my_config)
        assert model.statistics.output_files
        return self.get_actual_path(id) + "tab_{id}.px".format(id=id)

    def test_cube_101_ok(self):
        path = self.build("101")
        assert _data_section(path).strip()

    def test_cube_102_ok(self):
        path = self.build("102")
        assert _data_section(path).strip()

    def test_cube_103_ok(self):
        path = self.build("103")
        assert _data_section(path).strip()

    def test_cube_104_same_data_as_103_despite_shuffled_csv(self):
        # 104 shuffles the input CSV rows/columns compared to 103, but the
        # resulting DATA matrix must be identical since it represents the
        # same logical data.
        path_103 = self.build("103")
        path_104 = self.build("104")
        assert _data_section(path_103) == _data_section(path_104)

    def test_cube_130_as_103_but_with_stupid_columnnames_csv(self):
        path_103 = self.build("103")
        path_130 = self.build("130")
        assert _data_section(path_103) == _data_section(path_130)

    def test_cube_131_same_data_as_130_regardless_of_csv_or_parquet_source(self):
        # 130 and 131 are the same data delivered as CSV vs. parquet with
        # deliberately awkward column names; only the source format differs.
        path_130 = self.build("130")
        path_131 = self.build("131")
        assert _data_section(path_130) == _data_section(path_131)
