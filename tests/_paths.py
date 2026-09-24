import json
from pathlib import Path
from typing import Any


TESTDATA_ROOT = Path(__file__).parent / "testdata"


def data_path(*parts: str) -> Path:
    return TESTDATA_ROOT.joinpath(*parts)


def load_testdata_config(config_path: Path, output_dir: Path) -> dict[str, Any]:
    with config_path.open(encoding="utf-8-sig") as config_file:
        config = json.load(config_file)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_format = str(output_dir)
    config["admin"]["outputDestination"] = {
        "resourceType": "folders",
        "pxFolderFormat": output_format,
        "aggFolderFormat": output_format,
    }
    return config