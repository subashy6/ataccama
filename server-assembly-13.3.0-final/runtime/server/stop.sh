#!/bin/sh
#stops online server with preset values
cd ..
DQC_HOME=.
./bin/onlinectl.sh -config ./server/etc/default.serverConfig stop
cd server