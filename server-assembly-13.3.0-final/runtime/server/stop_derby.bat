@echo off

rem stops standalone derby database server

cd ..

set DQC_HOME=.
set JRE_HOME=%DQC_HOME%\..\jre

set JAVA_OPTS=-Dderby.system.home="%DQC_HOME%/../derby"

"%DQC_HOME%\bin\run_java.bat" org.apache.derby.iapi.tools.run server shutdown