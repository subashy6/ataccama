@echo off

rem Transformation utility

call "%~dp0\run_java.bat" com.ataccama.dqc.tools.xsl.XslTransform %*
