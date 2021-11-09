#!/usr/bin/env bash

# wrapper script for running class in yarn-cluster mode
# called by remote executor with arguments:
# $1 jar of bootstrap class
# $2 bootstrap class (RunnerMain)
# $3 properties file (temporary)
# $4 the runner class (IRemoteRunner impl)
# $* arguments for runner class

MYLIB=$1
CLASS=$2
PROPF=$3
LAUNCH=${4:-com.ataccama.dqc.spark.launch.LaunchModelSPCF}
shift
shift
shift
shift

MYDIR=`dirname $0`

source $MYDIR/hadoop_classpath_func.sh

# The folder with hadoop client configuration files.
# Is not needed to modify in default installation
export HADOOP_CONF_DIR=$MYDIR/client_conf/

# Check if client_conf folder contains need hadoop configuration and copy if needed
checkHadoopClientConfig

if [ "$SPARK_HOME" = "" ]; then
    findSparkHome
fi

if [ "$SPARK_SUBMIT" = "" ]; then
    SPARK_SUBMIT=spark-submit
fi

if [ "$ENABLE_DEBUG_LOGGING" = "true" ]; then
    LOG4J_FILE_NAME="spark_log4j_debug.properties"
else
    LOG4J_FILE_NAME="spark_log4j.properties"
fi

# debug trace driver
DEBUG=${DEBUG:-0}

if [ "$DEBUG" -gt 0 ]; then
    SPARK_DRIVER_JAVA_OPTS="-Dlog4j.configuration=file:$MYDIR/$LOG4J_FILE_NAME -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=$DEBUG"
else
    SPARK_DRIVER_JAVA_OPTS="-Dlog4j.configuration=file:$MYDIR/$LOG4J_FILE_NAME"
fi

exec $SPARK_HOME/bin/$SPARK_SUBMIT --files $MYDIR/$LOG4J_FILE_NAME --driver-java-options "$SPARK_DRIVER_JAVA_OPTS" --class $CLASS $MYLIB $PROPF $LAUNCH $*
