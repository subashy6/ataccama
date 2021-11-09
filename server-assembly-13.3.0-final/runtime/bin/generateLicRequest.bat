@echo off

rem License request generator

call "%~dp0\run_java.bat" com.ataccama.dqc.processor.bin.GenerateLicenseRequest %*
