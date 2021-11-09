#!/bin/sh

# modify JAVA_OPTS to meet your needs (such as heap size settings, variables definitions, etc.)
export JAVA_OPTS=-Xmx256M

#on VMS systems double quote the classname!

"${0%/*}/run_java.sh" com.ataccama.dqc.tasks.identify.bin.RepositoryUtil "$@"
