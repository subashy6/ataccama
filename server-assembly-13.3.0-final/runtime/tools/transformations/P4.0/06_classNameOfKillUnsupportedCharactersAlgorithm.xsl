<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="2.0"
	exclude-result-prefixes="xs xdt err fn"
	xmlns:err="http://www.w3.org/2005/xqt-errors"
	xmlns:fn="http://www.w3.org/2005/xpath-functions"	
	xmlns:xdt="http://www.w3.org/2005/xpath-datatypes"	
	xmlns:xs="http://www.w3.org/2001/XMLSchema"	
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:ver="http://www.ataccama.com/purity/version"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Changes v1.clean.KillUnsupportedCharactersAlgorithm to the current">
	
	<!--
		Nahradi attribut
			'cz.adastra.cif.tasks.v1.clean.KillUnsupportedCharactersAlgorithm'
		aktualnim	
	    	'cz.adastra.cif.tasks.clean.KillUnsupportedCharactersAlgorithm'
	-->

	<xsl:template match="//@className">
		<xsl:choose>
			<xsl:when test=".=&quot;cz.adastra.cif.tasks.v1.clean.KillUnsupportedCharactersAlgorithm&quot;">
				<xsl:attribute name="className">cz.adastra.cif.tasks.clean.KillUnsupportedCharactersAlgorithm</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:attribute name="className">
					<xsl:value-of select="."/>
				</xsl:attribute>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
