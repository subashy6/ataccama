@echo off
rem
rem Server service intaller
rem If no command is passed to the Launcher the GUI (attended version) is run. 
rem If you need to run unattended installation, specify the command and needed attributes using the following syntax:
rem 
rem java -classpath common\cif-commons.jar;common\cif-server-service-wrapper.jar com.ataccama.server.service.runtime.Launcher [options] <command>
rem
rem Commands
rem    install			  install the service
rem    uninstall          uninstalls the service
rem    help               prints out help/syntax information
rem
rem Attributes
rem   -serviceName		  name of the service to install. Mandatory in INSTALL mode only.
rem   -serverDir          server directory - directory containing service wrapper files. Directory must have same structure as
rem                       the <product>/runtime/server directory
rem   -serverConfigFile   server configuration file
rem   -licensesDir        directory containing locense files to use for the server startup
rem   -libsDir            directory containing product's libraries
rem   -jreDir             directory containing java runtime environment to use for running the server
rem   -jvmArgs            arguments to be passed to the JVM when starting the server
rem
rem
rem	To fill the GUI installer with predefined values, run the command with related attributes defined but without specfying the command.
rem To print out the installer's help use 



@SETLOCAL ENABLEEXTENSIONS
@cd /d "%~dp0"

NET SESSION >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
   set INITIAL_CLASSPATH=$INITIAL_CLASSPATH;cif-server-service-wrapper.jar
   ..\..\bin\run_java.bat com.ataccama.server.service.runtime.Launcher %*
) ELSE (
    ECHO Insufficient credentials. Please close this script and run it again as administrator.
    pause
)
