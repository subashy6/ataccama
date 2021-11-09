@echo off

rem DQC Repository utility

set JAVA_OPTS=-Xmx256M

call "%~dp0\run_java.bat" com.ataccama.profiling.results.storage.ExportProfile %*
