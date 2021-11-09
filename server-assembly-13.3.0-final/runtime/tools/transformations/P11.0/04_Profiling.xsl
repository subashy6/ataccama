<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.0.0" ver:versionTo="11.0.0"
	ver:name="Add new node and attribute into profiling config">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.profiling.ProfilingAlgorithm']">
		<step id="{@id}" className="com.ataccama.dqc.tasks.profiling.ProfilingAlgorithm" disabled="{@disabled}" mode="{@mode}">
			<properties defaultLocale="{properties/@defaultLocale}" outputLimit="{if(properties/@outputLimit != '') then properties/@outputLimit else '1000'}" threaded="{properties/@threaded}"> 
				<xsl:if test="properties/tableNamePrefix|properties/@tableNamePrefix!=''"><xsl:attribute name="tableNamePrefix" select="properties/@tableNamePrefix|properties/tableNamePrefix"/></xsl:if>
				<xsl:if test="properties/dataSource|properties/@dataSource!=''"><xsl:attribute name="dataSource" select="properties/@dataSource|properties/dataSource"/></xsl:if>
				<xsl:if test="properties/outputFile|properties/@outputFile!=''"><xsl:attribute name="outputFile" select="properties/@outputFile|properties/outputFile"/></xsl:if>	
				
				<businessDomains looseThreshold="20.0" strictThreshold="25.0"/>
				<xsl:copy-of select="properties/domains"/>
				<xsl:copy-of select="properties/fkAnalysis"/>
				<xsl:copy-of select="properties/inputs"/>
				<xsl:copy-of select="properties/masks"/>			
				<xsl:copy-of select="properties/userMetadata"/>	
				<xsl:copy-of select="properties/*[name()='comm:comment']"/>				
			</properties>
			<xsl:copy-of select="visual-constraints"/>
		</step>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" />
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
