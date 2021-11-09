#!/bin/bash

#find DQC_HOME if not given
if [ -z "$DQC_HOME" ]; then
	# find full path of this script using variable modification (remove suffix of the form '/*'
	DQC_HOME=${0%/*}/..
fi

#prepare CLASSPATH (only cif.boostrap*.jar)
export CLASSPATH="$(ls $DQC_HOME/lib/boot/cif?bootstrap*.jar)":$INITIAL_CLASSPATH

#java executable
if [ -z "$JAVA_HOME" ] ; then
	if [ -f "$DQC_HOME/../jre/bin/java" ] ; then
	  JAVA_EXE=$DQC_HOME/../jre/bin/java
  else
    JAVA_EXE=java
	fi
else
	JAVA_EXE=$JAVA_HOME/bin/java
fi

#run java
echo "Using java at: "$JAVA_EXE
echo "Using DQC  at: "$DQC_HOME

$JAVA_EXE $JAVA_OPTS "com.ataccama.dqc.bootstrap.DqcBootstrap" "$DQC_HOME" "$@"
