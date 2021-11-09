<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: 'quantilesCount' to 'percentileCount'">
<!-- 
	    nahrada quantilesCount za percentileCount  - nejprve v elementech a pak v atributech
  -->
	<xsl:template match="percentileCount">
		<quantilesCount>
			<xsl:value-of select="."/>
		</quantilesCount>
	</xsl:template>
	<xsl:template match="@percentileCount">
		<xsl:attribute name="quantilesCount">
			<xsl:value-of select="."/>
		</xsl:attribute>
	</xsl:template>
	
<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
