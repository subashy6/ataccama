#!/bin/bash
"/runtime/bin/onlinectl.sh" -config /runtime/server/etc/default.serverConfig start
if [ ! $? == 0 ]; then
	echo "Server startup failed. Press Enter when ready"
	read a
fi
