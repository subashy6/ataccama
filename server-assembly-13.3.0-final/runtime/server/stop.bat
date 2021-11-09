@echo off
rem stops online server with preset values
cd ..
set DQC_HOME=.
call bin\onlinectl.bat -config .\server\etc\default.serverConfig stop
cd server