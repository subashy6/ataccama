#!/bin/bash
export DQC_HOME=runtime
"$DQC_HOME/bin/onlinectl.sh" -config /runtime/server/etc/default.serverConfig stop
