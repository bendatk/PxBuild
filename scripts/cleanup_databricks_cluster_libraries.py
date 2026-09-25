"""Mark stale pxbuild wheel libraries for uninstall on the spark-test clusters.

Each `databricks bundle deploy --target spark_tests` builds a wheel with a new
dynamic version (see `databricks.yml`) and installs it on the existing test
clusters. Databricks never removes a previously installed library on its own,
so the cluster's library list grows by one wheel per deploy.

This script inspects each configured cluster, finds every installed
`pxbuild-*.whl` library except the one that matches the wheel just built in
`dist/`, and calls `databricks libraries uninstall` for the rest. Per the
Databricks Libraries API, uninstall only takes effect after the cluster is
next restarted; this script does not restart clusters.

Usage:
    uv run python scripts/cleanup_databricks_cluster_libraries.py \
        --profile <profile-name> --target spark_tests
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys


def databricks_cli(args: list[str], profile: str | None) -> str:
    cmd = ["databricks", *args, "-o", "json"]
    if profile:
        cmd += ["--profile", profile]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def load_variable_overrides(target: str) -> dict[str, str]:
    path = os.path.join(
        ".databricks", "bundle", target, "variable-overrides.json"
    )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def current_wheel_name() -> str:
    matches = sorted(glob.glob(os.path.join("dist", "*.whl")))
    if not matches:
        raise SystemExit("No wheel found in dist/. Run `uv build` first.")
    return os.path.basename(matches[-1])


def cleanup_cluster(cluster_id: str, keep_wheel: str, profile: str | None) -> None:
    library_statuses = json.loads(
        databricks_cli(["libraries", "cluster-status", cluster_id], profile)
    )
    stale = [
        lib["library"]
        for lib in library_statuses
        if "whl" in lib.get("library", {})
        and os.path.basename(lib["library"]["whl"]).startswith("pxbuild-")
        and os.path.basename(lib["library"]["whl"]) != keep_wheel
    ]
    if not stale:
        print(f"{cluster_id}: nothing to clean up")
        return
    payload = {"cluster_id": cluster_id, "libraries": stale}
    databricks_cli(
        ["libraries", "uninstall", "--json", json.dumps(payload)], profile
    )
    print(f"{cluster_id}: marked {len(stale)} stale pxbuild wheel(s) for uninstall")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--target", default="spark_tests")
    args = parser.parse_args()

    overrides = load_variable_overrides(args.target)
    keep_wheel = current_wheel_name()
    for key in ("cluster_id_15_4", "cluster_id_16_4", "cluster_id_17_3"):
        cleanup_cluster(overrides[key], keep_wheel, args.profile)

    print(
        "Uninstall requests are pending; the cluster library list only "
        "clears once each cluster is restarted."
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(exc.stderr, file=sys.stderr)
        sys.exit(exc.returncode)


