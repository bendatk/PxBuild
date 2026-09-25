import json
from pathlib import Path
from typing import Any


TESTDATA_ROOT = Path(__file__).parent / "testdata"
REPOSITORY_ROOT = TESTDATA_ROOT.parent.parent


def data_path(*parts: str) -> Path:
    return TESTDATA_ROOT.joinpath(*parts)


def load_testdata_config(config_path: Path, output_dir: Path | None = None) -> dict[str, Any]:
    with config_path.open(encoding="utf-8-sig") as config_file:
        config = json.load(config_file)

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_format = str(output_dir)
        config["admin"]["outputDestination"] = {
            "resourceType": "folders",
            "pxFolderFormat": output_format,
            "aggFolderFormat": output_format,
        }
        return config

    output_destination = config["admin"]["outputDestination"]
    for key in ("pxFolderFormat", "aggFolderFormat"):
        output_template = output_destination[key]
        output_path = Path(output_template)
        path_for_validation = output_template.replace("{id}", "__pxbuild_test_id__")
        if output_path.is_absolute():
            resolved_path = Path(path_for_validation).resolve()
        else:
            resolved_path = (REPOSITORY_ROOT / path_for_validation).resolve()

        if REPOSITORY_ROOT.resolve() not in resolved_path.parents:
            raise ValueError(f"Test output path must be inside the repository: {resolved_path}")

        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        output_destination[key] = str(resolved_path).replace("__pxbuild_test_id__", "{id}")

    return config