#!/bin/bash

# Transformation utility

"${0%/*}/run_java.sh" com.ataccama.dqc.tools.xsl.XslTransform "$@"
