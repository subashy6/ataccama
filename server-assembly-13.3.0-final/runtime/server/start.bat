@echo off
rem starts online server with preset values
cd ..
set DQC_HOME=.
set JAVA_OPTS=-Dlogging.logbackExtensionFile=server\etc\logback-extension.xml
call bin\onlinectl.bat -config .\server\etc\default.serverConfig start
cd server