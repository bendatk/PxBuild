import pxbuild


class TestCubes2nn:
    # 200: many notes and metaid

    def set_path(self) -> None:
        # pytest dont like dunder init
        self._my_path = "testdata/test_cubes_2nn/"
        self._my_config = self._my_path + "config.json"

    def get_actual_path(self, id: str) -> str:
        return "testdata/out_files/cubes_2nn/test_cube_{id}/".format(id=id)

    def test_cube_200_ok(self):
        self.set_path()
        model = pxbuild.build_px_file("200", self._my_config)

        assert model.statistics.output_files
        file = self.get_actual_path("200") + "tab_200.px"
        with open(file, encoding="iso-8859-1") as fh:
            content = fh.read()

        # Spot-check that the various NOTE/VALUENOTE/CELLNOTE/META-ID
        # keywords this cube is specifically about were actually written.
        expected_fragments = [
            'NOTEX[en]="Another note. On all of the cube. Mandatory.";',
            'NOTE[en]="A note. On all of the cube. not Mandatory";',
            'VALUENOTEX[en]("contents","Measure 1")="Another note. On Measure 1. Mandatory.";',
            'VALUENOTE[en]("contents","Measure 1")="A note. On Measure 1. not Mandatory";',
            'CELLNOTE[en]("Code 1 for dim 1","Code 2 for dim 2","Code 3 for dim 3","2000","Measure 2")='
            '"A cellnote. On 2000, Measure2, dim1:01, dim2:02 and dim3:03. not Mandatory";',
            'META-ID("urn:ssb:metaId_on_table urn:ssb:metaId_in_statistics")="tablelevel";',
            'META-ID[en]("contents","Measure 1")="urn:ssb:metaId_on_Measure1";',
        ]
        for fragment in expected_fragments:
            assert fragment in content, fragment + " missing from tab_200.px"
