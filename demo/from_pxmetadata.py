from pathlib import Path
from pxbuild.control.from_pxmetadata import PxBuildModel, build_px_file
import pandas as pd
import json

project_root = Path(__name__).resolve().parents[0]
dataframe = pd.read_parquet(project_root / "tests/testdata/real_world/11lv/11lv.parquet")
id = '11lv'

with open(file=project_root / "tests/testdata/real_world/11lv/config.json") as f:
    config = json.load(f)

metadata = config["admin"]["pxMetadataResource"]["adressFormat"]
metadata["dataset"]["dataFile"] = {id: dataframe}

config["admin"]["pxDataResource"] = {
    "resourceType": "dataframe",
    "adressFormat": "",
}

config["admin"]["outputDestination"] = {
    "resourceType": None,
    "pxFolderFormat": str(project_root / f"demo/{id}"),
    "aggFolderFormat": str(project_root / f"demo/{id}")
}


model: PxBuildModel = build_px_file(
    pxmetadata_id=id,
    config_file=config,
    backend='pandas',
    debug=True
)

print(model.validation_by_language)

print(model.statistics)

print(model.table_id)
print(model.get_model().title.get_value(model.main_language))
print(model.get_model().contents.get_value(model.main_language))
for note_key, note_value in model.get_model().note.get_sorted_value_by_key().items():
    print(f"{note_key.variable}[{note_key.lang}]: {note_value.get_value()}")