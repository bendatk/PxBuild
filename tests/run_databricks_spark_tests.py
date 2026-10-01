"""Run Spark integration tests from a synced Azure Databricks bundle."""

import importlib.util
import os
import sys
from pathlib import Path


def _register_tests_package(workspace_root: Path) -> None:
    tests_dir = workspace_root / "tests"
    init_file = tests_dir / "__init__.py"
    if not init_file.is_file():
        raise SystemExit(f"Synced tests package is missing: {init_file}")

    spec = importlib.util.spec_from_file_location(
        "tests",
        init_file,
        submodule_search_locations=[str(tests_dir)],
    )
    if spec is None or spec.loader is None:
        raise SystemExit(f"Unable to load synced tests package: {init_file}")

    tests_package = importlib.util.module_from_spec(spec)
    sys.modules["tests"] = tests_package
    spec.loader.exec_module(tests_package)

    paths_file = tests_dir / "_paths.py"
    paths_spec = importlib.util.spec_from_file_location("tests._paths", paths_file)
    if paths_spec is None or paths_spec.loader is None:
        raise SystemExit(f"Unable to load synced test path helper: {paths_file}")

    paths_module = importlib.util.module_from_spec(paths_spec)
    sys.modules["tests._paths"] = paths_module
    paths_spec.loader.exec_module(paths_module)


def _assert_installed_pxbuild(workspace_root: Path) -> None:
    import pxbuild

    package_path = Path(pxbuild.__file__).resolve()
    if package_path.is_relative_to(workspace_root):
        raise SystemExit(f"pxbuild must be imported from the installed wheel, not synced source: {package_path}")


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: run_spark_tests.py <bundle-workspace-path> <spark-temp-volume> <runtime>")

    workspace_root = Path(sys.argv[1])
    if not workspace_root.is_dir():
        raise SystemExit(f"Bundle workspace path does not exist: {workspace_root}")
    runtime = sys.argv[3]
    if not runtime or "/" in runtime or "\\" in runtime:
        raise SystemExit(f"Invalid Databricks runtime label: {runtime!r}")

    runtime_volume_path = Path(sys.argv[2]) / f"dbr-{runtime}"
    runtime_volume_path.mkdir(parents=True, exist_ok=True)

    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["PXBUILD_SPARK_TEMP_VOLUME"] = str(runtime_volume_path)
    os.chdir(workspace_root)
    _register_tests_package(workspace_root)
    _assert_installed_pxbuild(workspace_root)

    import pytest

    return pytest.main(["-p", "no:cacheprovider", "-o", "addopts=", "-m", "databricks", "tests/spark"])


if __name__ == "__main__":
    # Databricks runs spark_python_task files inside an IPython shell, which treats
    # any raised SystemExit as a failed run even when the code is 0.
    exit_code = main()
    if exit_code != 0:
        raise SystemExit(exit_code)
