# Spark Hadoop configuration

This directory contains several files that are used for launching Spark jobs on Hadoop cluster.
If you want to use Spark on Hadoop in DPE, please enable **SPARK_HADOOP** profile in `application.properties` and configure properly `application-SPARK_HADOOP.properties` configuration file.

**Content of the directory:**
* `exec_spark2.sh` - This file is an entry script for launching Spark jobs in DPE.
* `hadoop_classpath_func.sh` - The shell script contains various utilities like discovering SPARK_HOME, validating spark properties and others which are used during the launch of a job in `exec_spark2.sh` script.
* `spark_log4j.properties` - Standard Log4j configuration for Spark job.
* `spark_log4j_debug.properties` - Log4j configuration for Spark job that is used if the jobs are running in debug mode (more info about debug mode in `application-SPRING_HADOOP.properties`).
* `copy_client_conf.sh` - If you launch the script it will attempt to copy system Hadoop client configuration files into `client_conf` directory.
* `load_default_spark_properties.sh` - This utility will copy default Spark properties into `spark.properties` file. If you want to use these properties in the actual configuration please put them into `application-SPRING_HADOOP.properties` file. Please use prefix `plugin.executor-launch-model.ataccama.one.launch-type-properties.SPARK.` for the properties.
