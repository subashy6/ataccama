<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Renames path variable prefix - purity: to pathvar:."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="properties//*[starts-with(.,'purity://')]">
		<xsl:copy><xsl:apply-templates select="@*"/><xsl:value-of select="concat('pathvar://',substring(.,10))"/></xsl:copy>
	</xsl:template>
	<xsl:template match="properties//@*[starts-with(.,'purity://')]">
		<xsl:attribute name="{name()}"><xsl:value-of select="concat('pathvar://',substring(.,10))"/></xsl:attribute>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
