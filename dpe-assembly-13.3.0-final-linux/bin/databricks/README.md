# Databricks launch script

This directory contains `exec_databricks.sh` shell script that is used for the launch of Spark jobs running via Databricks.

To use Databricks in DPE please enable **SPARK_DATABRICKS** profile in `application.properties` and specify the correct path to the shell script in `application-SPARK_DATABRICKS.properties`.

Example:
```properties
plugin.executor-launch-model.ataccama.one.launch-type-properties.SPARK.exec=bin/databricks/exec_databricks.sh
```
