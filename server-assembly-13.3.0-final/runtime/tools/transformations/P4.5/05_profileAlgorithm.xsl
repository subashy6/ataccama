<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.0" ver:versionTo="4.5.0"
	ver:name="Renames extremeCount/quantilesCount to extremes/quantiles in ProfilingAlgorithm">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']/properties">
		<xsl:element name="properties">
			<xsl:apply-templates mode="rename" select="*|@*" />
		</xsl:element>
	</xsl:template>

	<xsl:template mode="rename" match="standardStats/extremeCount|standardStats/@extremeCount">
			<xsl:attribute name='extremes'><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>

	<xsl:template mode="rename" match="standardStats/quantilesCount|standardStats/@quantilesCount">
			<xsl:attribute name='quantiles'><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>

	<xsl:template mode="rename" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="rename" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>