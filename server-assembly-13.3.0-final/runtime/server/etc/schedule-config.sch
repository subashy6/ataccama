<?xml version='1.0' encoding='UTF-8'?>
<scheduleDefinition>
    <description>some schedule description (will be shown on the Admin Center)</description>
    <enabled>true</enabled>
      <!--
      <job class="job_class">
            ... job configuration goes here, see individual job configurations bellow ...
      </job>
      -->    
    <scheduling>33 10 4 * </scheduling>
</scheduleDefinition>
<!--
    RunShellScriptJob:
    Job executes Unix-like script.It uses temporary script file to execute specified commands
    (script file is created in the Job's resources directory). This script file is then passed
    to the selected interpreter (/bin/sh) by default)
-->
<!--
<job class="com.ataccama.adt.scheduler.job.RunShellScriptJob">
    <command>/development/releases/start.sh</command>
    <workingDir>server</workingDir>
    <interpreter>/bin/bash</interpreter>
    <logStartStop>true</logStartStop>
</job>
-->
 
<!--
    RunWinCmdJob:
    Job executes Windows shell command. It utilizes temporary script file
    (created in the Job's resources folder) to execute more complex scripts and return
    correct return-value using exit %ERRORLEVEL% instruction.
-->
<!--
<job class="com.ataccama.adt.scheduler.job.RunWinCmdJob">
    <command>D:\development\releases\start.exe"</command>
    <workingDir>d:\var\server</workingDir>
    <logStartStop>true</logStartStop>
</job>
 -->

<!--
    Run Workflow Job:
    Job runs workflow of the server's workflow component (it means: workflow must be known
    to the workflow server component because it is executed from there)
-->
<!--
<job class="com.ataccama.adt.scheduler.job.WorkflowJob">
    <!- - for workflows coming from a named source use sourceId:workflowName notation, e.g. source1:myWorkflow.ewf - ->
    <workflow>simple-params.ewf</workflow>
    <variables>
        <variable name="command1" value="notepad"/>
        <variable name="command2" value="notepad"/>
    </variables>
</job>
-->
