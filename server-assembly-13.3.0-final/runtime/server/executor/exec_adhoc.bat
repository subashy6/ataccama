@rem echo off
setlocal enabledelayedexpansion

@rem wrapper script for adhoc running class
@rem called by remote executor with arguments:
@rem $1 jar of bootstrap class
@rem $2 bootstrap class (RunnerMain)
@rem $3 properties file (temporary)
@rem $4 the runner class (IRemoteRunner impl)
@rem $* arguments for runner class

set MYDIR=%~dp0

@rem ---------------------- USER DEFINED PARAMETERS ---------------

@rem Set Java if needed.
@rem set JAVA_HOME=/usr/java/jdk1.8.0_65

@rem ------------------------ SYSTEM SETTINGS ---------------------

set MAINCP=%1%
set CLASS=%2%
set PROPF=%3%
shift /1
shift /1
shift /1

echo %*

@rem debug trace driver
@rem if NOT DEFINED DEBUG set DEBUG=0

@rem java executable
set JAVA_EXE=java
if DEFINED JAVA_HOME set JAVA_EXE=%JAVA_HOME%\bin\java

set CLASSPATH="%MAINCP%";%CLASSPATH%;"%DQC_HOME%"\lib\*

if DEFINED DEBUG set DEBUG_OPT=-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=%DEBUG%

@rem skip first three args - %* ignores shifting in windows' cmd
set ARGS=
set /a idx=0
for %%I in (%*) do (
	set /a "idx+=1"
	if !idx! gtr 3 set ARGS=!ARGS! %%I
)
echo ARGS: %ARGS%

"%JAVA_EXE%" -classpath %CLASSPATH% %DEBUG_OPT% %CLASS% %PROPF% %ARGS%
