#!/usr/bin/env bash

# wrapper script for adhoc running class
# called by remote executor with arguments:
# $1 jar of bootstrap class
# $2 bootstrap class (RunnerMain)
# $3 properties file (temporary)
# $4 the runner class (IRemoteRunner impl)
# $* arguments for runner class

MYDIR=`dirname "$0"`

#---------------------- USER DEFINED PARAMETERS ---------------

# Set Java if needed.
#export JAVA_HOME=/usr/java/jdk1.8.0_65

#------------------------ SYSTEM SETTINGS ---------------------
MYLIB=$1
CLASS=$2
PROPF=$3
LAUNCH=${4:-com.ataccama.dqc.hadoop.launch.LaunchModelRL}
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


export CLASSPATH="$MYLIB":$CLASSPATH

[ "$DEBUG" -gt 0 ] && DEBUG_OPT=-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=$DEBUG

$JAVA_EXE $JAVA_OPTS $DEBUG_OPT $CLASS "$PROPF" $LAUNCH "$@"