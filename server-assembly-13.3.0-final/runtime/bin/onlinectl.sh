#!/bin/sh

# modify JAVA_OPTS to meet your needs (such as heap size settings, variables definitions, etc.)
# export JAVA_OPTS=
# Sample JPDA settings for remote socket debuging
# export JAVA_OPTS="$JAVA_OPTS -Xdebug -Xrunjdwp:transport=dt_socket,address=8787,server=y,suspend=n"

#on VMS systems double quote the classname!

"${0%/*}/run_java.sh" com.ataccama.dqc.server.bin.OnlineCtl "$@"
