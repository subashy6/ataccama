<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Renames drillDown to drillThrough"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']/properties/inputs/*/drillDown">
		<xsl:element name="drillThrough"><xsl:value-of select="." /></xsl:element>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']/properties/inputs/*/@drillDown">
		<xsl:attribute name="drillThrough"><xsl:value-of select="." /></xsl:attribute>
	</xsl:template>
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']/properties/inputs/*/drillDownLimit">
		<xsl:element name="drillThroughLimit"><xsl:value-of select="." /></xsl:element>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']/properties/inputs/*/@drillDownLimit">
		<xsl:attribute name="drillThroughLimit"><xsl:value-of select="." /></xsl:attribute>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>