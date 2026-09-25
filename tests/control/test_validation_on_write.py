from types import SimpleNamespace
from unittest.mock import patch
from typing import Any

import pytest

from pxbuild import PxBuildValidationError
from pxbuild.control.from_pxmetadata import ValidationSummary, write_px_file


def test_write_px_file_rejects_invalid_model_before_writing() -> None:
    validation_by_language = {
        "en": ValidationSummary(
            is_valid=False,
            passed_count=4,
            failed_count=1,
            errors=["Validation failed: missing CONTENTS."],
        )
    }
    model: Any = SimpleNamespace(is_valid=False, validation_by_language=validation_by_language)

    with patch("pxbuild.control.from_pxmetadata.write_output") as write_output:
        with pytest.raises(PxBuildValidationError) as error:
            write_px_file(model)

    write_output.assert_not_called()
    assert error.value.validation_by_language == validation_by_language
    assert "Language en:" in str(error.value)
    assert "missing CONTENTS" in str(error.value)
