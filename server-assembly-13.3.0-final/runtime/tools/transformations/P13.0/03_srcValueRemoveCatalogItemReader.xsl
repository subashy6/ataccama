<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:fn="http://www.w3.org/2005/xpath-functions"
	ver:versionFrom="13.0.0" ver:versionTo="13.1.0"
	ver:name="Remove src value from CatalogItemReader"
        exclude-result-prefixes="ver xsl fn">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.catalogItems.CatalogItemReader']/properties/columns/catalogItemColumn">
		<catalogItemColumn>
			<xsl:copy-of select="@*[not(name()='src')]"/>
			<xsl:copy-of select="node()"/>
		</catalogItemColumn>
	</xsl:template>
	
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>