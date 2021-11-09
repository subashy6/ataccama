<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="2.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.0.0" ver:versionTo="10.1.0"
	ver:name="Upgrade workflow tasks">

	<xsl:template match="@*|node()">
		<xsl:copy>
  			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
 	</xsl:template>
	
	<xsl:template match="task[executable/@class='com.ataccama.adt.task.exec.EwfForEachTask']">
		<task>
		<xsl:if test="id or @id!=''"><xsl:attribute name="id" select="@id|id"/></xsl:if>
		<xsl:if test="priority or @priority!=''"><xsl:attribute name="priority" select="@priority|priority"/></xsl:if>
		<xsl:if test="acceptMode or @acceptMode!=''"><xsl:attribute name="acceptMode" select="@acceptMode|acceptMode"/></xsl:if>
		<xsl:if test="description or @description!=''"><xsl:attribute name="description" select="@description|description"/></xsl:if>
		<xsl:if test="name or @name!=''"><xsl:attribute name="name" select="@name|name"/></xsl:if>		
			<executable workflowId="{executable/@workflowId|executable/workflowId}" class="{executable/@class|executable/class}" breakOnError="{executable/@breakOnError|executable/breakOnError}">
				<xsl:attribute name="iterationType">
					<xsl:choose>
						<xsl:when test="lower-case(executable/@iterationType)='serial' or lower-case(executable/iterationType)='serial'">
							<xsl:value-of select="'SERIAL'"/>
						</xsl:when>
						<xsl:when test="lower-case(executable/@iterationType)='parallel' or lower-case(executable/iterationType)='parallel'">
							<xsl:value-of select="'PARALLEL'"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="'SERIAL'"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>
				<xsl:choose>
					<xsl:when test="executable/iterable/@class='com.ataccama.adt.task.iterators.FileIterator'">
						<iterable recursive="{executable/iterable/@recursive|executable/iterable/recursive}" directory="{executable/iterable/@directory|executable/iterable/directory}" mask="{executable/iterable/@mask|executable/iterable/mask}" class="{executable/iterable/@class|executable/iterable/class}">
							<parameterMapping>
								<parameters>
									<xsl:for-each select="executable/iterable/mapper/variables/variableMapping">
										<parameter expression="{@source|source}" name="{@variable|variable}">
											<xsl:copy-of select="*[name()='comm:comment']"/>
										</parameter>
									</xsl:for-each>
									<xsl:copy-of select="executable/iterable/mapper/variables/*[name()='comm:comment']"/>
								</parameters>
								<xsl:copy-of select="executable/iterable/mapper/*[name()='comm:comment']"/>
							</parameterMapping>
							<xsl:copy-of select="executable/iterable/*[name()='comm:comment']"/>
						</iterable>
					</xsl:when>
					<xsl:when test="executable/iterable/@class='com.ataccama.adt.task.iterators.SetIterator'">
						<iterable set="{executable/iterable/@set|executable/iterable/set}" class="{executable/iterable/@class|executable/iterable/class}" separator="{executable/iterable/@separator|executable/iterable/separator}">
							<parameterMapping>
								<parameters>
									<xsl:for-each select="executable/iterable/mapper/variables/variableMapping">
										<parameter expression="{@source|source}" name="{@variable|variable}">
											<xsl:copy-of select="*[name()='comm:comment']"/>
										</parameter>
									</xsl:for-each>
									<xsl:copy-of select="executable/iterable/mapper/variables/*[name()='comm:comment']"/>
								</parameters>
								<xsl:copy-of select="executable/iterable/mapper/*[name()='comm:comment']"/>
							</parameterMapping>
							<xsl:copy-of select="executable/iterable/*[name()='comm:comment']"/>
						</iterable>
					</xsl:when>
					<xsl:when test="executable/iterable/@class='com.ataccama.adt.task.iterators.SqlRowIterator'">
						<iterable query="{executable/iterable/@query|executable/iterable/query}" class="{executable/iterable/@class|executable/iterable/class}" connectionName="{executable/iterable/@connectionName|executable/iterable/connectionName}">
							<parameterMapping>
								<parameters>
									<xsl:for-each select="executable/iterable/mapper/variables/variableMapping">
										<parameter expression="{@source|source}" name="{@variable|variable}">
											<xsl:copy-of select="*[name()='comm:comment']"/>
										</parameter>
									</xsl:for-each>
									<xsl:copy-of select="executable/iterable/mapper/variables/*[name()='comm:comment']"/>
								</parameters>
								<xsl:copy-of select="executable/iterable/mapper/*[name()='comm:comment']"/>
							</parameterMapping>
							<xsl:copy-of select="executable/iterable/*[name()='comm:comment']"/>
						</iterable>
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
</xsl:stylesheet>

