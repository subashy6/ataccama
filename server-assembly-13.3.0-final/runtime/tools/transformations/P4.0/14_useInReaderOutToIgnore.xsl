<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: 'useInReaderOut' to 'ignore'">
	
	<!--
	    nahrada useInReaderOut za ignore
	-->

	<xsl:template match="@useInReaderOut">
		<xsl:variable name="useInReaderOut" select="." />
		
		<xsl:attribute name='ignore'>
			<xsl:call-template name="negate">
				<xsl:with-param name="flag" select="$useInReaderOut" />
			</xsl:call-template>
		</xsl:attribute>
	</xsl:template>

	<xsl:template match="step[contains(@className, 'TextFileReader')]/properties/columns/column">
		<xsl:variable name="useInReaderOut" select="@useInReaderOut" />
		
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" />
		
			<xsl:if test="not($useInReaderOut)">
				<xsl:attribute name='ignore'>false</xsl:attribute>
			</xsl:if>

		</xsl:copy>
		
	</xsl:template>
	
	<!-- negate true/false values -->
	<xsl:template name="negate">
		<xsl:param name="flag" />
	
		<xsl:choose>
			<xsl:when test="$flag = 'true'">false</xsl:when>
			<xsl:otherwise>true</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>