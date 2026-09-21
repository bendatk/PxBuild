import re

import pxbuild

# Every top-level PX keyword expected to appear in a "real world" table, extracted
# from a reference production .px file. Only presence of the keyword is checked,
# not its value: this is an end-to-end smoke test for build_px_model/write_px_file/
# build_px_file using real Statistics Finland metadata, codelists and data (table
# "11lv" - adoptions), not a value-for-value comparison against the reference file
# (which is for an unrelated table, "11zj").
EXPECTED_KEYWORDS = [
    "AXIS-VERSION",
    "CODEPAGE",
    "CODES",
    "CONTACT",
    "CONTENTS",
    "CONTVARIABLE",
    "COPYRIGHT",
    "CREATION-DATE",
    "DATA",
    "DECIMALS",
    "DESCRIPTION",
    "ELIMINATION",
    "HEADING",
    "LANGUAGE",
    "LANGUAGES",
    "LAST-UPDATED",
    "MAP",
    "MATRIX",
    "META-ID",
    "NOTE",
    "OFFICIAL-STATISTICS",
    "PRECISION",
    "SHOWDECIMALS",
    "SOURCE",
    "STUB",
    "SUBJECT-AREA",
    "SUBJECT-CODE",
    "TABLEID",
    "TIMEVAL",
    "TITLE",
    "UNITS",
    "VALUENOTE",
    "VALUES",
    "VARIABLECODE",
    "VARIABLE-TYPE",
]

# MADE-WITH is a known gap: there is no output keyword/writer support for it yet
# anywhere in pxbuild, so no config can currently make it appear in a built file.
NOT_YET_IMPLEMENTED_KEYWORDS = ["MADE-WITH"]

PXMETADATA_ID = "11lv"
CONFIG_FILE = "testdata/test_11lv/config.json"


def _keyword_pattern(keyword: str) -> re.Pattern:
    # Match "KEYWORD=", "KEYWORD[lang]=" or "KEYWORD(" at the start of a line, so
    # that e.g. CODES doesn't false-positive-match on CODEPAGE, and NOTE doesn't
    # match VALUENOTE/VALUENOTEX.
    return re.compile(r"(^|\n)" + re.escape(keyword) + r"(\[[^\]]*\])?\s*(=|\()")


class TestEleventhLvKeywords:
    """End-to-end test of build_px_model / write_px_file / build_px_file.

    Uses real Statistics Finland metadata, codelists and a real (small) parquet
    dataset for table 11lv, copied into testdata/test_11lv/. Only the keyword
    names present in the output .px file are checked, not their values.
    """

    def test_build_px_model_produces_a_valid_in_memory_model(self):
        model = pxbuild.build_px_model(PXMETADATA_ID, CONFIG_FILE)

        assert model.pxmetadata_id == PXMETADATA_ID
        assert model.statistics.row_count == 9696
        assert model.statistics.output_files == []

    def test_write_px_file_writes_the_model_built_by_build_px_model(self):
        model = pxbuild.build_px_model(PXMETADATA_ID, CONFIG_FILE)

        written_files = pxbuild.write_px_file(model)

        assert written_files
        assert model.statistics.output_files == written_files
        assert model.statistics.write_seconds is not None

    def test_build_px_file_output_contains_all_expected_keywords(self):
        model = pxbuild.build_px_file(PXMETADATA_ID, CONFIG_FILE)

        assert model.statistics.output_files
        out_file = model.statistics.output_files[0]

        with open(out_file, encoding="utf-8-sig") as fh:
            content = fh.read()

        missing = [kw for kw in EXPECTED_KEYWORDS if not _keyword_pattern(kw).search(content)]
        assert not missing, f"Missing expected keywords in output: {missing}"

        # Keywords known to not be implemented yet must stay absent; if one starts
        # appearing, this assertion (and NOT_YET_IMPLEMENTED_KEYWORDS above) should
        # be updated to reflect the new implementation.
        still_missing = [kw for kw in NOT_YET_IMPLEMENTED_KEYWORDS if not _keyword_pattern(kw).search(content)]
        assert still_missing == NOT_YET_IMPLEMENTED_KEYWORDS
