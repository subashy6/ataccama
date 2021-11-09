#!/bin/sh
#starts online server with preset values

#check if running in silent mode to redirect logs
for i in "$@" 
do
case $i in
        -s|--silent)
        SILENT="true"
        ;;
esac
done

cd ..
DQC_HOME=.
JAVA_OPTS="-Dlogging.logbackExtensionFile=server/etc/logback-extension.xml"
export DQC_HOME JAVA_OPTS
COMMAND="./bin/onlinectl.sh -config ./server/etc/default.serverConfig start"
if [ "$SILENT" = "true" ]; then
        exec $COMMAND >> ./server/logs/server.out 2>&1 &
        echo "Server is starting. Please check the log file in [DQC_HOME]/server/logs/ folder"
else
        exec $COMMAND
fi
cd server
