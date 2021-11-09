#!/bin/sh

# modify JAVA_OPTS to meet your needs (such as heap size settings, variables definitions, etc.)
export JAVA_OPTS="-Xms256M -Xmx1024M"

#on VMS systems double quote the classname!

"${0%/*}/run_java.sh" com.ataccama.dqc.addresses.v1.bin.CifPrepareFiles "$@"
