# Azure Databricks Spark Tests

The Azure Databricks bundle runs `tests/spark` as parallel tasks on existing
Databricks Runtime clusters, each targeting a separately tested runtime
version. The job uses native cluster PySpark. Runtimes 15.4, 16.4, and 17.3
are currently tested against; the exact set of versions may change over time.

## Why existing clusters instead of job clusters

The three tasks target already-running clusters (`existing_cluster_id`) rather
than letting the job spin up its own ephemeral job clusters. Job clusters take
several minutes to start, and during active development that startup cost
would be paid on every test iteration. Keeping the clusters warm also means
`pytest` and the `pxbuild` runtime dependencies only need to be installed once
per cluster, instead of being reinstalled from scratch on every fresh job cluster.
The tradeoff is the cluster library accumulation problem described below,
since existing clusters are not torn down after each run.

## Why an asset bundle

- The bundle runs the full `pytest` suite natively, in parallel, against
  every supported runtime version in a single job run, which is what
  actually needs verifying across runtime versions.
- The bundle is a declarative, version-controlled job definition, so the same
  `databricks bundle deploy && databricks bundle run` invocation used locally
  can later be dropped into merge/pull request CI automation without
  rewriting the test orchestration.

Each task installs the built `pxbuild` wheel. The bundle syncs the test runner,
tests, and test data only; it does not sync the `pxbuild/` source tree. This
ensures the remote tests exercise the installed artifact.

Before running the bundle, install `pytest` on each existing test cluster. The `pxbuild`
runtime dependencies must also already be present on those clusters. The bundle
does not install packages directly from PyPI.

Authenticate the Databricks CLI against the Azure Databricks workspace:

```bash
databricks auth login --host https://adb-<workspace-id>.<region>.azuredatabricks.net
```

Set the three existing cluster IDs locally in the ignored
`.databricks/bundle/spark_tests/variable-overrides.json` file:

```json
{
	"cluster_id_15_4": "<cluster-id>",
	"cluster_id_16_4": "<cluster-id>",
	"cluster_id_17_3": "<cluster-id>",
	"spark_temp_volume": "/Volumes/<catalog>/<schema>/<volume>/pxbuild-spark-tests/"
}
```

The configured Volume must grant the job identity `READ VOLUME` and `WRITE
VOLUME`. Each parallel task creates a runtime-specific parent directory such as
`dbr-15.4/` and then uses unique child directories for its staged Parquet data,
Spark part files, and generated output. The test removes its unique child
directories after completion.

Then validate, deploy, and run the job:

```bash
databricks bundle validate --target spark_tests
databricks bundle deploy --target spark_tests
databricks bundle run --target spark_tests spark_integration_tests
```

Use `--profile <profile-name>` with each command when the workspace is not the
default Databricks CLI profile. The selected profile determines the target Azure
Databricks workspace. The cluster must permit the developer to attach and
install the task libraries. Bundle deployment uploads the project wheel and the
`tests/` tree; generated output remains in pytest temporary directories.

Because `dynamic_version: true` gives every deploy a unique wheel filename, and
the three tasks target existing (not job-managed) clusters, each deploy adds a
new `pxbuild-*.whl` library entry that Databricks never removes on its own.
After testing session, mark the previous wheels for uninstall:

```bash
uv run python scripts/cleanup_databricks_cluster_libraries.py --target spark_tests
```

Use `--profile <profile-name>` if needed. Per the Databricks Libraries API, an
uninstall request only takes effect the next time the cluster restarts, so
stale entries remain visible in the cluster's Libraries UI until someone
restarts it; the script does not restart clusters itself.
