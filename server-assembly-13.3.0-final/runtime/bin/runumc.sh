#!/bin/bash

# modify JAVA_OPTS to meet your needs (such as heap size settings, variables definitions, etc.)
# export JAVA_OPTS=

#on VMS systems double quote the classname!

"${0%/*}/run_java.sh" com.ataccama.web.amc.core.util.UmcAdmin "$@"