@echo off

rem DQC file preparation task for updating UIR-ADR source files

rem modify JAVA_OPTS to meet your needs (such as heap size settings, variables definitions, etc.)
set JAVA_OPTS=-Xms256M -Xmx1024M

call "%~dp0\run_java.bat" com.ataccama.dqc.addresses.v1.bin.CifPrepareFiles %*
