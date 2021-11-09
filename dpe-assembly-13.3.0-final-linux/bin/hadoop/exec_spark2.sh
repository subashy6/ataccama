#!/usr/bin/env bash

# wrapper script for running class in spark context
# called by remote executor with arguments:
# $1 jar of bootstrap class
# $2 bootstrap class (RunnerMain)
# $3 properties file (temporary)
# $4 the runner class (IRemoteRunner impl)
# $* arguments for runner class

MYLIB=$1
CLASS=$2
PROPF=$3
LAUNCH=${4:-com.ataccama.dqc.spark.launch.LaunchModelSP}
shift
shift
shift
shift

MYDIR=`dirname $0`
source $MYDIR/hadoop_classpath_func.sh

# The folder with hadoop client configuration files.
# Is not needed to modify in default installation
export HADOOP_CONF_DIR=$MYDIR/client_conf/

if [ "$SPARK_SUBMIT" = "" ]; then
    SPARK_SUBMIT=spark-submit
fi

# check if client_conf folder contain need hadoop configuration and copy if needed
checkHadoopClientConfig


# Spark folder which contains hadoop client configuration files
# Does not need to be set up by default
if [ "$ENABLE_SPARK_CONF_DIR" = "true" ]; then
    export SPARK_CONF_DIR=$HADOOP_CONF_DIR
fi

#Script will validate spark configuration
if ! [ "$DISABLE_VALIDATE_SPARK_PROPERTIES" = "true" ]; then
    validateSparkProperties "$PROPF"
fi


if [ "$SPARK_HOME" = "" ]; then
	findSparkHome
fi

if [ "$ENABLE_SPARK_DIST_CLASSPATH" = "true" ]; then
    export SPARK_DIST_CLASSPATH=`hadoop classpath`
fi

if ! [ "$SET_SPARK_DIST_CLASSPATH" = "" ]; then
    export SPARK_DIST_CLASSPATH=$SET_SPARK_DIST_CLASSPATH
fi

if [ "$ENABLE_DEBUG_LOGGING" = "true" ]; then
    LOG4J_FILE_NAME="spark_log4j_debug.properties"
else
	LOG4J_FILE_NAME="spark_log4j.properties"
fi


#---------------------- Hadoop Automatic Classpath ------------


# Defines hadoop classpath used for local processings
enableLocalHadoopClasspath


# Set excluded runtime libs (variable used in .properties file)
export EXCLUDE_FROM_RUNTIME='!hive-jdbc*:!jboss*:!slf4j*:!commons-lang3*:!scala*:!kryo*'

#------------------------ SYSTEM SETTINGS ---------------------



# debug trace driver
DEBUG=${DEBUG:-0}

if [ "$DEBUG" -gt 0 ]; then
        SPARK_DRIVER_JAVA_OPTS="--driver-java-options -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=$DEBUG"
else
        SPARK_DRIVER_JAVA_OPTS="--driver-java-options -Dlog4j.configuration=file:$MYDIR/$LOG4J_FILE_NAME"
fi
COMMAND="$SPARK_HOME/bin/$SPARK_SUBMIT \
		--files $MYDIR/$LOG4J_FILE_NAME $SPARK_DRIVER_JAVA_OPTS $SPARK_DRIVER_OPTS \
        --class $CLASS $JARS $MYLIB $PROPF $LAUNCH $*";
exec $COMMAND
