#!/usr/bin/env bash

# wrapper script for running class in map-reduce context
# called by remote executor with arguments:
# $1 jar of bootstrap class
# $2 bootstrap class (RunnerMain)
# $3 properties file (temporary)
# $4 the runner class (IRemoteRunner impl)
# $* arguments for runner class

MYDIR=`dirname $0`

#---------------------- USER DEFINED PARAMETERS ---------------

# Set Java if needed.
#export JAVA_HOME=/usr/java/jdk1.8.0_65

# The folder with hadoop client configuration files.
# Is not needed to modify in default installation
export HADOOP_CONF_DIR=$MYDIR/client_conf/

#---------------------- Hadoop Automatic Classpath ------------
source $MYDIR/hadoop_classpath_func.sh

# Defines classpath for Hive libraries via 'hcat -classpath' command. 
# Writes the classpath to $HIVE_CLUSTER_CP variable
enableMRHiveLibs

# Defines classpath for HBase libraries via 'hbase classpath' command. 
# Writes the classpath to $HBASE_CLUSTER_CP variable
enableHBaseLibs

# Defines classpath for hadoop libraries via 'hadoop classpath' command. 
# Writes the classpath to $LOCAL_CP variable which is used as local classpath only.
enableLocalHadoopClasspath

# Set excluded runtime libs (variable used in .properties file)
export EXCLUDE_FROM_RUNTIME='!hive-jdbc*:!jboss*:!slf4j*:!commons-lang3*'

#------------------------ SYSTEM SETTINGS ---------------------
MYLIB=$1
CLASS=$2
PROPF=$3
LAUNCH=${4:-com.ataccama.dqc.hadoop.launch.LaunchModelMR}
shift
shift
shift
shift

# debug trace driver
DEBUG=${DEBUG:-0}

#java executable
if [ -z "$JAVA_HOME" ] ; then
        JAVA_EXE=java
else
        JAVA_EXE=$JAVA_HOME/bin/java
fi


export CLASSPATH=$CLASSPATH:$HADOOP_CONF_DIR:$LOCAL_CP:$MYLIB
echo "cp.hive_jars=$HIVE_CLUSTER_CP" >> $PROPF
echo "cp.hbase_jars=$HBASE_CLUSTER_CP" >> $PROPF

[ "$DEBUG" -gt 0 ] && DEBUG_OPT=-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=$DEBUG

exec $JAVA_EXE $DEBUG_OPT $CLASS $PROPF $LAUNCH $*
