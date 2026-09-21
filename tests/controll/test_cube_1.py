import pxbuild


class TestCube1:
    def test_cube_1_dont_crash(self):
        model = pxbuild.build_px_file("1", "testdata/test_cube_1/test_config.json")

        assert model.statistics.output_files
