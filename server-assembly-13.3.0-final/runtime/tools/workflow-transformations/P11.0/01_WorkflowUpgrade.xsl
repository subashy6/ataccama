<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="2.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.1.0" ver:versionTo="11.0.0"
	ver:name="Upgrade workflow tasks">

	<xsl:template match="@*|node()">
		<xsl:copy>
  			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
 	</xsl:template>
	
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfFileOperationTask']">	
		<task>
		<xsl:if test="id or @id!=''"><xsl:attribute name="id" select="@id|id"/></xsl:if>
		<xsl:if test="priority or @priority!=''"><xsl:attribute name="priority" select="@priority|priority"/></xsl:if>
		<xsl:if test="acceptMode or @acceptMode!=''"><xsl:attribute name="acceptMode" select="@acceptMode|acceptMode"/></xsl:if>
		<xsl:if test="description or @description!=''"><xsl:attribute name="description" select="@description|description"/></xsl:if>
		<xsl:if test="name or @name!=''"><xsl:attribute name="name" select="@name|name"/></xsl:if>	
		<xsl:if test="disabled or @disabled!=''"><xsl:attribute name="disabled" select="@disabled|disabled"/></xsl:if>
		<xsl:if test="mode or @mode!=''"><xsl:attribute name="mode" select="if(@mode|mode) then @mode|mode else 'NORMAL'"/></xsl:if>		
			<executable class="{executable/@class}">
				<xsl:choose>
					<xsl:when test="executable/@operation='MOVE' or executable/operation='MOVE'">					
						<operation overwriteFlag="{executable/@overwriteFlag|executable/overwriteFlag}" sourceFile="{executable/@sourceFile|executable/sourceFile}" class="com.ataccama.adt.file.operations.EwfMoveFileOperation" targetFile="{executable/@targetFile|executable/targetFile}"/>
					</xsl:when>
					<xsl:when test="executable/@operation='ZIP' or executable/operation='ZIP'">					
						<operation overwriteFlag="{executable/@overwriteFlag|executable/overwriteFlag}" sourceFile="{executable/@sourceFile|executable/sourceFile}" recursiveFlag="{executable/@recursiveFlag|executable/recursiveFlag}" class="com.ataccama.adt.file.operations.EwfZipFileOperation" targetFile="{executable/@targetFile|executable/targetFile}">
							<excludeParameters>
								<xsl:for-each select="executable/excludeParameters/string">						
									<string><xsl:value-of select="."/></string>
								</xsl:for-each>
							</excludeParameters>
						</operation>										
					</xsl:when>
					<xsl:when test="executable/@operation='UNZIP' or executable/operation='UNZIP'">					
						<operation overwriteFlag="{executable/@overwriteFlag|executable/overwriteFlag}" sourceFile="{executable/@sourceFile|executable/sourceFile}" class="com.ataccama.adt.file.operations.EwfUnzipFileOperation" targetFile="{executable/@targetFile|executable/targetFile}"/>										
					</xsl:when>
					<xsl:when test="executable/@operation='EXISTS' or executable/operation='EXISTS'">					
						<operation sourceFile="{executable/@sourceFile|executable/sourceFile}" class="com.ataccama.adt.file.operations.EwfExistFileOperation"/>		`												
					</xsl:when>
					<xsl:when test="executable/@operation='NOT_EXISTS' or executable/operation='NOT_EXISTS'">					
						<operation sourceFile="{executable/@sourceFile|executable/sourceFile}" class="com.ataccama.adt.file.operations.EwfNotExistFileOperation"/>										
					</xsl:when>
					<xsl:when test="executable/@operation='MKDIR' or executable/operation='MKDIR'">					
						<operation recursiveFlag="{executable/@recursiveFlag|executable/recursiveFlag}" class="com.ataccama.adt.file.operations.EwfMkdirOperation" targetFile="{executable/@targetFile|executable/targetFile}"/>					
					</xsl:when>
					<xsl:when test="executable/@operation='DELETE' or executable/operation='DELETE'">
						<operation recursiveFlag="{executable/@recursiveFlag|executable/recursiveFlag}" class="com.ataccama.adt.file.operations.EwfDeleteFileOperation" targetFile="{executable/@targetFile|executable/targetFile}"/>
					</xsl:when>
					<xsl:when test="executable/@operation='COPY' or executable/operation='COPY'">					
						<operation overwriteFlag="{executable/@overwriteFlag|executable/overwriteFlag}" sourceFile="{executable/@sourceFile|executable/sourceFile}" recursiveFlag="{executable/@recursiveFlag|executable/recursiveFlag}" class="com.ataccama.adt.file.operations.EwfCopyFileOperation" targetFile="{executable/@targetFile|executable/targetFile}"/>										
					</xsl:when>
					<xsl:when test="executable/@operation='FILE_INFO' or executable/operation='FILE_INFO'">					
						<operation sourceFile="{executable/@sourceFile|executable/sourceFile}" class="com.ataccama.adt.file.operations.EwfFileInfoOperation"/>										
					</xsl:when>	
					<xsl:otherwise>				
					</xsl:otherwise>																											
				</xsl:choose>	
			</executable>				
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</task>		
	</xsl:template>	
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfWaitForFileTask']">	
		<task>
		<xsl:if test="id or @id!=''"><xsl:attribute name="id" select="@id|id"/></xsl:if>
		<xsl:if test="priority or @priority!=''"><xsl:attribute name="priority" select="@priority|priority"/></xsl:if>
		<xsl:if test="acceptMode or @acceptMode!=''"><xsl:attribute name="acceptMode" select="@acceptMode|acceptMode"/></xsl:if>
		<xsl:if test="description or @description!=''"><xsl:attribute name="description" select="@description|description"/></xsl:if>
		<xsl:if test="name or @name!=''"><xsl:attribute name="name" select="@name|name"/></xsl:if>	
		<xsl:if test="disabled or @disabled!=''"><xsl:attribute name="disabled" select="@disabled|disabled"/></xsl:if>
		<xsl:if test="mode or @mode!=''"><xsl:attribute name="mode" select="if(@mode|mode) then @mode|mode else 'NORMAL'"/></xsl:if>	
			<executable fileName="{executable/@fileName|executable/fileName}" class="{executable/@class|executable/class}">
				<xsl:choose>
					<xsl:when test="executable/@waitFor=''"><xsl:attribute name="waitFor" select="'APPEAR'"/></xsl:when>
					<xsl:when test="executable/waitFor='DISAPPEAR' or executable/@waitFor='DISAPPEAR'"><xsl:attribute name="waitFor" select="'DISAPPEAR'"/></xsl:when>
					<xsl:when test="not(executable/waitFor)"><xsl:attribute name="waitFor" select="'APPEAR'"/></xsl:when>
					<xsl:when test="executable/waitFor='DISAPPEAR' or executable/@waitFor='DISAPPEAR'"><xsl:attribute name="waitFor" select="'DISAPPEAR'"/></xsl:when>
					<xsl:otherwise><xsl:attribute name="waitFor" select="'APPEAR'"/></xsl:otherwise>
				</xsl:choose>
				<xsl:if test="executable/@timeout!='' or executable/timeout!=''">
					<xsl:attribute name="timeout" select="if(executable/@timeout!='0' or executable/timeout!='0') then executable/@timeout|executable/timeout else executable/@timeout|executable/timeout"/>
				</xsl:if>
				<xsl:if test="executable/@pollingInterval!='' or executable/pollingInterval!=''">
					<xsl:attribute name="pollingInterval" select="if(executable/@pollingInterval!='0' or executable/pollingInterval!='0') then executable/@pollingInterval|executable/pollingInterval else executable/@pollingIntervalExpression|executable/pollingIntervalExpression"/>
				</xsl:if>			
			</executable>			
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</task>
	</xsl:template>			
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfWaitForHDFSFileTask']">	
		<task>
		<xsl:if test="id or @id!=''"><xsl:attribute name="id" select="@id|id"/></xsl:if>
		<xsl:if test="priority or @priority!=''"><xsl:attribute name="priority" select="@priority|priority"/></xsl:if>
		<xsl:if test="acceptMode or @acceptMode!=''"><xsl:attribute name="acceptMode" select="@acceptMode|acceptMode"/></xsl:if>
		<xsl:if test="description or @description!=''"><xsl:attribute name="description" select="@description|description"/></xsl:if>
		<xsl:if test="name or @name!=''"><xsl:attribute name="name" select="@name|name"/></xsl:if>	
		<xsl:if test="disabled or @disabled!=''"><xsl:attribute name="disabled" select="@disabled|disabled"/></xsl:if>
		<xsl:if test="mode or @mode!=''"><xsl:attribute name="mode" select="if(@mode|mode) then @mode|mode else 'NORMAL'"/></xsl:if>	
			<executable fileName="{executable/@fileName|executable/fileName}" class="{executable/@class|executable/class}">
				<xsl:choose>
					<xsl:when test="executable/@waitFor=''"><xsl:attribute name="waitFor" select="'APPEAR'"/></xsl:when>
					<xsl:when test="executable/waitFor='DISAPPEAR' or executable/@waitFor='DISAPPEAR'"><xsl:attribute name="waitFor" select="'DISAPPEAR'"/></xsl:when>
					<xsl:when test="not(executable/waitFor)"><xsl:attribute name="waitFor" select="'APPEAR'"/></xsl:when>
					<xsl:when test="executable/waitFor='DISAPPEAR' or executable/@waitFor='DISAPPEAR'"><xsl:attribute name="waitFor" select="'DISAPPEAR'"/></xsl:when>
					<xsl:otherwise><xsl:attribute name="waitFor" select="'APPEAR'"/></xsl:otherwise>
				</xsl:choose>				
				<xsl:if test="executable/@timeout!='' or executable/timeout!=''">
					<xsl:attribute name="timeout" select="if(executable/@timeout!='0' or executable/timeout!='0') then executable/@timeout|executable/timeout else executable/@timeout|executable/timeout"/>
				</xsl:if>
				<xsl:if test="executable/@pollingInterval!='' or executable/pollingInterval!=''">
					<xsl:attribute name="pollingInterval" select="if(executable/@pollingInterval!='0' or executable/pollingInterval!='0') then executable/@pollingInterval|executable/pollingInterval else executable/@pollingIntervalExpression|executable/pollingIntervalExpression"/>
				</xsl:if>			
			</executable>
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</task>
	</xsl:template>	
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfWaitForSqlRowTask']">	
		<task>
		<xsl:if test="id or @id!=''"><xsl:attribute name="id" select="@id|id"/></xsl:if>
		<xsl:if test="priority or @priority!=''"><xsl:attribute name="priority" select="@priority|priority"/></xsl:if>
		<xsl:if test="acceptMode or @acceptMode!=''"><xsl:attribute name="acceptMode" select="@acceptMode|acceptMode"/></xsl:if>
		<xsl:if test="description or @description!=''"><xsl:attribute name="description" select="@description|description"/></xsl:if>
		<xsl:if test="name or @name!=''"><xsl:attribute name="name" select="@name|name"/></xsl:if>	
		<xsl:if test="disabled or @disabled!=''"><xsl:attribute name="disabled" select="@disabled|disabled"/></xsl:if>
		<xsl:if test="mode or @mode!=''"><xsl:attribute name="mode" select="if(@mode|mode) then @mode|mode else 'NORMAL'"/></xsl:if>	
			<executable query="{executable/@query|executable/query}" class="com.ataccama.adt.task.exec.EwfWaitForSqlRowTask" connectionName="{executable/@connectionName|executable/connectionName}">
				<xsl:if test="executable/@timeout!='' or executable/timeout!=''">
					<xsl:attribute name="timeout" select="if(executable/@timeout!='0' or executable/timeout!='0') then executable/@timeout|executable/timeout else executable/@timeout|executable/timeout"/>
				</xsl:if>
				<xsl:if test="executable/@pollingInterval!='' or executable/pollingInterval!=''">
					<xsl:attribute name="pollingInterval" select="if(executable/@pollingInterval!='0' or executable/pollingInterval!='0') then executable/@pollingInterval|executable/pollingInterval else executable/@pollingIntervalExpression|executable/pollingIntervalExpression"/>
				</xsl:if>				
				<xsl:copy-of select="executable/mapping"/>			
			</executable>
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</task>
	</xsl:template>		
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfWaitForSqlValueTask']">	
		<task>
		<xsl:if test="id!='' or @id!=''"><xsl:attribute name="id" select="@id|id"/></xsl:if>
		<xsl:if test="priority!='' or @priority!=''"><xsl:attribute name="priority" select="@priority|priority"/></xsl:if>
		<xsl:if test="acceptMode!='' or @acceptMode!=''"><xsl:attribute name="acceptMode" select="@acceptMode|acceptMode"/></xsl:if>
		<xsl:if test="description!='' or @description!=''"><xsl:attribute name="description" select="@description|description"/></xsl:if>
		<xsl:if test="name!='' or @name!=''"><xsl:attribute name="name" select="@name|name"/></xsl:if>	
		<xsl:if test="disabled!='' or @disabled!=''"><xsl:attribute name="disabled" select="@disabled|disabled"/></xsl:if>
		<xsl:if test="mode!='' or @mode!=''"><xsl:attribute name="mode" select="if(@mode|mode) then @mode|mode else 'NORMAL'"/></xsl:if>	
			<executable condition="{executable/@condition|executable/condition}" query="{executable/@query|executable/query}" class="com.ataccama.adt.task.exec.EwfWaitForSqlValueTask" connectionName="{executable/@connectionName|executable/connectionName}">
				<xsl:if test="executable/@timeout!='' or executable/timeout!=''">
					<xsl:attribute name="timeout" select="if(executable/@timeout!='0' or executable/timeout!='0') then executable/@timeout|executable/timeout else executable/@timeout|executable/timeout"/>
				</xsl:if>
				<xsl:if test="executable/@pollingInterval!='' or executable/pollingInterval!=''">
					<xsl:attribute name="pollingInterval" select="if(executable/@pollingInterval!='0' or executable/pollingInterval!='0') then executable/@pollingInterval|executable/pollingInterval else executable/@pollingIntervalExpression|executable/pollingIntervalExpression"/>
				</xsl:if>				
				<xsl:copy-of select="executable/mapping"/>			
			</executable>
			<xsl:copy-of select="resources"/>
			<xsl:copy-of select="*[name()='vis:visualConstraints']"/>
			<xsl:copy-of select="*[name()='comm:comment']"/>
		</task>
	</xsl:template>
</xsl:stylesheet>

