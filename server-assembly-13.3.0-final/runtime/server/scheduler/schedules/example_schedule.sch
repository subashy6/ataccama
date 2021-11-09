<?xml version='1.0' encoding='UTF-8'?>
<scheduleDefinition>
    <description>First schedule</description>
    <enabled>true</enabled>
    <job class="com.ataccama.adt.scheduler.job.RunWinCmdJob">
		<command>../resources/greeting.bat</command>
		<workingDir>.</workingDir>
		<logStartStop>false</logStartStop>
	</job>
    <scheduling>* 11 * * </scheduling>
</scheduleDefinition>