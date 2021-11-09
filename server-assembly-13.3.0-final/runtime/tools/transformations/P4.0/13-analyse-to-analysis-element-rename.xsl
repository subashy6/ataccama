<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.16" ver:versionTo="4.0.17"
	ver:name="Rename frequency analysis elements: from 'analyse' to 'analysis'">
	
	<!--
	    nahrada analyse za analysis v elementech
	-->
	<xsl:template match="analyse">
		<analysis>
			<xsl:apply-templates select="*|@*|comment()|text()"/>
		</analysis>
	</xsl:template>
	
	<xsl:template match="@analyse">
		<xsl:attribute name='analysis'><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="*|@*|comment()|text()"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>