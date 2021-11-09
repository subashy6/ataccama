@echo off

rem Encryption utility

call "%~dp0\run_java.bat" com.ataccama.dqc.commons.bin.EncryptString %*
