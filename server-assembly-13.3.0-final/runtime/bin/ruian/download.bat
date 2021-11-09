@echo off

rem Script for RUIAN download

rem modify JAVA_OPTS to meet your needs (such as heap size settings, variables definitions, etc.)
rem set JAVA_OPTS=

call "%~dp0..\run_java.bat" com.ataccama.dqc.tasks.addresses.ruian.DownloadRuian %* 