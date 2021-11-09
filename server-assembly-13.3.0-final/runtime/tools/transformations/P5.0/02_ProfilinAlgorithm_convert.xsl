<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.0" ver:versionTo="5.0.0"
	ver:name="Converts ProfilinAlgorithm to the new version">

	<xsl:template match="//step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="pr" />
		</xsl:copy>
	</xsl:template>

	<xsl:template match="@outputXml" mode="pr">
		<xsl:attribute name="outputFile"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>

	<xsl:template match="outputXml" mode="pr">
		<xsl:element name="outputFile"><xsl:value-of select="."/></xsl:element>
	</xsl:template>

	<xsl:template match="properties/dataToProfile" mode="pr">
		<xsl:element name="inputs">
			<xsl:element name="profilingInput">
				<xsl:attribute name="name">in</xsl:attribute>
				<xsl:element name="dataToProfile">
					<xsl:apply-templates select="node()" mode="pr" />
				</xsl:element>
			</xsl:element>
		</xsl:element>
	</xsl:template>

	<xsl:template match="standardStats/count|standardStats/@count" mode="pr">
		<xsl:attribute name="extremes"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>

	<xsl:template match="standardStats/quantilesCount|standardStats/@quantilesCount" mode="pr">
		<xsl:attribute name="quantiles"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>

	<xsl:template match="node()|@*" mode="pr">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="pr" />
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>