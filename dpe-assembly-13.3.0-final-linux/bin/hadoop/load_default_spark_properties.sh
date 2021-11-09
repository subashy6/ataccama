#!/usr/bin/env bash

# Specify the file path to spark-default.conf file
SPARK_DEFAULT_PROPS=/etc/spark2/conf/spark-defaults.conf


if [ -f "$SPARK_DEFAULT_PROPS" ]; then
    echo "spark-defaults.conf was found, loading..."
	cat $SPARK_DEFAULT_PROPS spark.properties > tmp_properties && mv tmp_properties spark.properties
	echo "properties were updated, please check spark.properties file if the settings are correct"
else
	echo "spark-defaults.conf was not found in the specified path: $SPARK_DEFAULT_PROPS. Please configure the location for the file in $SPARK_DEFAULT_PROPS variable inside this script"
fi