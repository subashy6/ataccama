<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="2.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="11.0.0" ver:versionTo="12.0.0"
	ver:name="Upgrade workflow tasks - transform old HDFS tasks to Operate On File and Wait For File tasks">

	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfWaitForHDFSFileTask']">	
		<xsl:element name="task">
			<xsl:attribute name="mode" select="@mode"/>
			<xsl:attribute name="acceptMode" select="@acceptMode"/>
			<xsl:attribute name="disabled" select="@disabled"/>
			<xsl:attribute name="id" select="@id"/>
			<xsl:attribute name="priority" select="@priority"/>
			<xsl:element name="executable">
				<xsl:attribute name="fileName" select="concat('resource://',executable/@hadoopSource ,executable/@fileName)"/>
				<xsl:attribute name="pollingInterval" select="executable/@pollingInterval"/>
				<xsl:attribute name="class" select="'com.ataccama.adt.task.exec.EwfWaitForFileTask'"/>
				<xsl:attribute name="waitFor" select="executable/@waitFor"/>
				<xsl:attribute name="timeout" select="executable/@timeout"/>
			</xsl:element>
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</xsl:element>
	</xsl:template>	
	
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfHDFSUploadFile']">	
		<xsl:element name="task">
			<xsl:attribute name="mode" select="@mode"/>
			<xsl:attribute name="acceptMode" select="@acceptMode"/>
			<xsl:attribute name="disabled" select="@disabled"/>
			<xsl:attribute name="id" select="@id"/>
			<xsl:attribute name="priority" select="@priority"/>
			<xsl:element name="executable">
			    <xsl:attribute name="class" select="'com.ataccama.adt.task.exec.EwfFileOperationTask'"/>
				<xsl:element name="operation">
					<xsl:attribute name="overwriteFlag" select="'false'"/>
					<xsl:attribute name="recursiveFlag" select="'false'"/>
					<xsl:attribute name="targetFile" select="concat('resource://',executable/@hadoopSource ,executable/@targetDirectory)"/>
					<xsl:attribute name="keepDirTreeFlag" select="'false'"/>
					<xsl:attribute name="class" select="'com.ataccama.adt.file.operations.EwfCopyFileOperation'"/>
					<xsl:attribute name="sourceFile" select="executable/@file"/>
				</xsl:element>
			</xsl:element>
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfHDFSDownloadFile']">	
		<xsl:element name="task">
			<xsl:attribute name="mode" select="@mode"/>
			<xsl:attribute name="acceptMode" select="@acceptMode"/>
			<xsl:attribute name="disabled" select="@disabled"/>
			<xsl:attribute name="id" select="@id"/>
			<xsl:attribute name="priority" select="@priority"/>
			<xsl:element name="executable">
			    <xsl:attribute name="class" select="'com.ataccama.adt.task.exec.EwfFileOperationTask'"/>
				<xsl:element name="operation">
					<xsl:attribute name="overwriteFlag" select="'false'"/>
					<xsl:attribute name="recursiveFlag" select="'false'"/>
					<xsl:attribute name="targetFile" select="executable/@targetDirectory"/>
					<xsl:attribute name="keepDirTreeFlag" select="'false'"/>
					<xsl:attribute name="class" select="'com.ataccama.adt.file.operations.EwfCopyFileOperation'"/>
					<xsl:attribute name="sourceFile" select="concat('resource://',executable/@hadoopSource ,executable/@file)"/>
				</xsl:element>
			</xsl:element>
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</xsl:element>
	</xsl:template>	
	
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.OperateOnHDFSFile']">
		<xsl:element name="task">
			<xsl:attribute name="mode" select="@mode"/>
			<xsl:attribute name="acceptMode" select="@acceptMode"/>
			<xsl:attribute name="disabled" select="@disabled"/>
			<xsl:attribute name="id" select="@id"/>
			<xsl:attribute name="priority" select="@priority"/>
			<xsl:element name="executable">
			    <xsl:attribute name="class" select="'com.ataccama.adt.task.exec.EwfFileOperationTask'"/>

				<xsl:choose>
					<xsl:when test="executable/operation/@class='com.ataccama.adt.task.operation.CopyOperation'">
						<xsl:element name="operation">	
							<xsl:attribute name="class" select="'com.ataccama.adt.file.operations.EwfCopyFileOperation'"/>	
							<xsl:attribute name="overwriteFlag" select="executable/operation/@overwrite"/>
							<xsl:attribute name="recursiveFlag" select="executable/operation/@recursive"/>
							<xsl:attribute name="keepDirTreeFlag" select="'false'"/> 
							<xsl:attribute name="sourceFile" select="concat('resource://', executable/@hadoopSource, executable/operation/@source)"/>		 
							<xsl:attribute name="targetFile" select="concat('resource://', executable/@hadoopSource, executable/operation/@target)"/> 
						</xsl:element>
					</xsl:when>				
					<xsl:when test="executable/operation/@class='com.ataccama.adt.task.operation.DeleteOperation'">
						<xsl:element name="operation">	
							<xsl:attribute name="class" select="'com.ataccama.adt.file.operations.EwfDeleteFileOperation'"/>	
							<xsl:attribute name="recursiveFlag" select="executable/operation/@recursive"/>
							<xsl:attribute name="targetFile" select="concat('resource://', executable/@hadoopSource, executable/operation/@target)"/>
						</xsl:element>
					</xsl:when>					
					<xsl:when test="executable/operation/@class='com.ataccama.adt.task.operation.FileExistOperation'">
						<xsl:element name="operation">	
							<xsl:attribute name="class" select="'com.ataccama.adt.file.operations.EwfExistFileOperation'"/>	
							<xsl:attribute name="sourceFile" select="concat('resource://', executable/@hadoopSource, executable/operation/@target)"/>		
						</xsl:element>
					</xsl:when>					
					<xsl:when test="executable/operation/@class='com.ataccama.adt.task.operation.FileNotExistOperation'">
						<xsl:element name="operation">	
							<xsl:attribute name="class" select="'com.ataccama.adt.file.operations.EwfNotExistFileOperation'"/>	
							<xsl:attribute name="sourceFile" select="concat('resource://', executable/@hadoopSource, executable/operation/@target)"/>	
						</xsl:element>
					</xsl:when>
					<xsl:when test="executable/operation/@class='com.ataccama.adt.task.operation.MkdirOperation'">
						<xsl:element name="operation">	
							<xsl:attribute name="class" select="'com.ataccama.adt.file.operations.EwfMkdirOperation'"/>	
							<xsl:attribute name="recursiveFlag" select="executable/operation/@recursive"/>
							<xsl:attribute name="targetFile" select="concat('resource://', executable/@hadoopSource, executable/operation/@target)"/>
						</xsl:element>
					</xsl:when>
					<xsl:when test="executable/operation/@class='com.ataccama.adt.task.operation.MoveOperation'">
						<xsl:element name="operation">	
							<xsl:attribute name="class" select="'com.ataccama.adt.file.operations.EwfMoveFileOperation'"/>	
							<xsl:attribute name="overwriteFlag" select="executable/operation/@overwrite"/>
							<xsl:attribute name="keepDirTreeFlag" select="'false'"/>
							<xsl:attribute name="sourceFile" select="concat('resource://', executable/@hadoopSource, executable/operation/@source)"/>		
							<xsl:attribute name="targetFile" select="concat('resource://', executable/@hadoopSource, executable/operation/@target)"/>
						</xsl:element>
					</xsl:when>	
				</xsl:choose>
				
			</xsl:element>
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</xsl:element>			
	</xsl:template>
	
	<xsl:template match="@*|node()">
		<xsl:copy>
  			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
 	</xsl:template>
	
</xsl:stylesheet>

