#!/bin/bash

# modify JAVA_OPTS to meet your needs (such as heap size settings, variables definitions, etc.)
# export JAVA_OPTS=

"${0%/*}/run_java.sh" "com.ataccama.epp.cli.bin.CsvExporter" "$@"
