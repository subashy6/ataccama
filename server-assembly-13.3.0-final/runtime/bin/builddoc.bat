@echo off

rem Build documentation utility

setlocal

set DOC_FOLDER=%~1
if "%DOC_FOLDER%" == "" set DOC_FOLDER=%~dp0\..\doc

call "%~dp0\run_java.bat" com.ataccama.dqc.doc.processor.bin.DocumentationProcessor "%DOC_FOLDER%"
