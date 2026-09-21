import pxbuild


class TestCube2:
    def test_cube_2_ok(self):
        model = pxbuild.build_px_file("2", "testdata/test_cube_2/test_config.json")

        assert model.statistics.output_files
        assert model.statistics.row_count > 0
        assert model.statistics.matrix_size > 0

        path_actual = model.statistics.output_files[0]
        with open(path_actual, encoding="iso-8859-1") as fh:
            content = fh.read()

        data_section = content.split("DATA=", 1)[1].rstrip().rstrip(";")
        # DATA cells are whitespace separated; formatting details (line
        # wrapping, trailing spaces, terminating ";") are not part of the
        # contract.
        actual_cells = data_section.split()

        expected_cells = (
            "1111 1112 1121 1122 1131 1132 "
            "1211 1212 1221 1222 1231 1232 "
            "1311 1312 1321 1322 1331 1332 "
            "2111 2112 2121 2122 2131 2132 "
            "2211 2212 2221 2222 2231 2232 "
            "2311 2312 2321 2322 2331 2332 "
            "3111 3112 3121 3122 3131 3132 "
            "3211 3212 3221 3222 3231 3232 "
            "3311 3312 3321 3322 3331 3332"
        ).split()

        assert actual_cells == expected_cells
