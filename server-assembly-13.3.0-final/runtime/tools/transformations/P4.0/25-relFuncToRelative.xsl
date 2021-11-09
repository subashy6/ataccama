<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: function='rel[Function]' to function='[function]' relative='true' (matching tests in UnifyEngine/SGC)">

	<!--
	    nahrada nazvu relativnich matching funkci za nerelativni nazev plus atribut relative='true'
	-->

	<xsl:template match="matchingRules/*/tests/*/@function[starts-with(.,'rel')]">
		<xsl:attribute name='relative'>true</xsl:attribute>
		<xsl:attribute name='function'><xsl:call-template name="nahrad"/></xsl:attribute>
	</xsl:template>

	<xsl:template match="matchingRules/*/tests/*/function[starts-with(.,'rel')]">
		<xsl:attribute name='relative'>true</xsl:attribute>
		<xsl:element name='function'><xsl:call-template name="nahrad"/></xsl:element>
	</xsl:template>

	<xsl:template name="nahrad">
		<xsl:value-of select="concat(translate(substring(., 4, 1), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), substring(., 5))"/>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>