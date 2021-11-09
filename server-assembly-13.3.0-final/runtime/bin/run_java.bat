@echo off

rem This script runs the product.
rem If necessary it searches for DQC_HOME and searches for JVM.
rem It uses DQcBootstrap to discover actual classpath

setlocal

call :guess_home
if "%DQC_HOME%" == "" goto :end

call :prepare_classpath

call :find_java
if "%JAVA_EXE%" == "" goto :end

call :standardize_path "%JAVA_EXE%"
call :standardize_dqc_home "%DQC_HOME%"

rem Launch java NOW!

echo Using java at: "%JAVA_EXE%"
echo Using DQC  at: "%DQC_HOME%"
"%JAVA_EXE%" %JAVA_OPTS% com.ataccama.dqc.bootstrap.DqcBootstrap "%DQC_HOME%/" %*

goto :end

rem ============================================================================
rem ============================================================================
rem Search for java executable

:find_java
if "%JAVA_HOME%" == "" goto :bundled_java

set JAVA_EXE=%JAVA_HOME%\bin\java.exe
if exist "%JAVA_EXE%" goto :found_java

:bundled_java
rem Java bundled with the product
set JAVA_EXE=%~dp0\..\..\jre\bin\java.exe
if exist "%JAVA_EXE%" goto :found_java

:system_java
rem Java on PATH?
call :which java.exe
if exist "%JAVA_EXE%" goto :found_java

echo Java executable not found
echo Please either set JAVA_HOME environment variable to point to your 
echo installation of Java or make sure you have installed the bundled 
echo JRE with the product.

set JAVA_EXE=

:found_java
goto :eof

rem ============================================================================
rem Standardize the path

:standardize_path
call set JAVA_EXE=%%~f1
goto :eof

:standardize_dqc_home
call set DQC_HOME=%%~f1
goto :eof

rem ============================================================================
rem Searches for a program (java.exe) in the system PATH

:which
call set JAVA_EXE=%~f$PATH:1
goto :eof

rem ============================================================================
rem Guess DQC home

:guess_home

if not "%DQC_HOME%" == "" goto gotHome
set DQC_HOME=%~dp0\..

:gotHome
if exist "%DQC_HOME%\bin\run_java.bat" goto :okHome

echo You must either set DQC_HOME environment variable
echo or run DQC from its installation folder.

set DQC_HOME=

:okHome
goto :eof

rem ============================================================================
rem Prepare classpath

:prepare_classpath
set CLASSPATH=
FOR /F "tokens=* USEBACKQ" %%F IN (`dir /B %DQC_HOME%\lib\boot\cif?bootstrap*.jar`) DO (
  SET cifboostrap=%DQC_HOME%\lib\boot\%%F
)
set CLASSPATH=%cifboostrap%;%INITIAL_CLASSPATH%
rem echo Using CLASSPATH=%CLASSPATH%

goto :eof

rem ============================================================================
rem Append to classpath

:append_cp
set CLASSPATH=%~1;%CLASSPATH%
goto :eof

:end
