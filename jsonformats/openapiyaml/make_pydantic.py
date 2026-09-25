from pathlib import Path
from datamodel_code_generator import generate, InputFileType, DataModelType, PythonVersion

generate(
    Path('jsonformats/openapiyaml/pxbuildconfig.yaml'),
    encoding='utf-8',
    input_file_type = InputFileType.OpenAPI,
    output = Path('pxbuild/models/input/pydantic_pxbuildconfig.py'),
    collapse_root_models=True,
    target_python_version=PythonVersion.PY_311,
    use_schema_description=True,
    use_field_description=True,
    snake_case_field=True,
    allow_population_by_field_name=True
)

generate(
    Path('jsonformats/openapiyaml/pxcodes.yaml'),
    encoding='utf-8',
    input_file_type = InputFileType.OpenAPI,
    output = Path('pxbuild/models/input/pydantic_pxcodes.py'),
    collapse_root_models=True,
    target_python_version=PythonVersion.PY_311,
    use_schema_description=True,
    use_field_description=True,
    snake_case_field=True,
    allow_population_by_field_name=True
)

generate(
    Path('jsonformats/openapiyaml/pxstatistics.yaml'),
    encoding='utf-8',
    input_file_type = InputFileType.OpenAPI,
    output = Path('pxbuild/models/input/pydantic_pxstatistics.py'),
    collapse_root_models=True,
    target_python_version=PythonVersion.PY_311,
    use_schema_description=True,
    use_field_description=True,
    snake_case_field=True,
    allow_population_by_field_name=True
)

generate(
    Path('jsonformats/openapiyaml/pxmetadata.yaml'),
    encoding='utf-8',
    input_file_type = InputFileType.OpenAPI,
    output = Path('pxbuild/models/input/pydantic_pxmetadata.py'),
    collapse_root_models=True,
    target_python_version=PythonVersion.PY_311,
    use_schema_description=True,
    use_field_description=True,
    snake_case_field=True,
    allow_population_by_field_name=True
)


# *** Scripts\datamodel-codegen.exe --input pxmetadata.yaml --input-file-type openapi --snake-case-field --encoding utf-8 --target-python-version 3.11 --collapse-root-models  --use-schema-description   --use-field-description  --output ..\..\pxbuild\models\input\pydantic_pxmetadata.py

# *** Scripts\datamodel-codegen.exe --input pxcodes.yaml --input-file-type openapi --snake-case-field --encoding utf-8 --target-python-version 3.11 --collapse-root-models  --use-schema-description   --use-field-description  --output  ..\..\pxbuild\models\input\pydantic_pxcodes.py 

# *** Scripts\datamodel-codegen.exe --input pxstatistics.yaml --input-file-type openapi --snake-case-field --encoding utf-8 --target-python-version 3.11 --collapse-root-models  --use-schema-description   --use-field-description  --output ..\..\pxbuild\models\input\pydantic_pxstatistics.py

# *** Scripts\datamodel-codegen.exe --input pxbuildconfig.yaml --input-file-type openapi --snake-case-field --encoding utf-8 --target-python-version 3.11 --collapse-root-models  --use-schema-description   --use-field-description  --output ..\..\pxbuild\models\input\pydantic_pxbuildconfig.py
