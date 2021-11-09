<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.0" ver:versionTo="4.6.0"
	ver:name="Removing lookupInfo property from SelectiveMatchingLookupBuider and SelectiveResLookupAlgorithm">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.SelectiveMatchingLookupBuilder']/properties">
		<xsl:element name="properties">
			<xsl:attribute name="outputColumn"><xsl:value-of select="lookupInfo/outputColumn|lookupInfo/@outputColumn"/></xsl:attribute>
			<xsl:attribute name="realValue"><xsl:value-of select="lookupInfo/realValue|lookupInfo/@realValue"/></xsl:attribute>
			<xsl:attribute name="fileName"><xsl:value-of select="lookupInfo/fileName|lookupInfo/@fileName"/></xsl:attribute>
			<xsl:apply-templates select="*|@*" mode="remove"/>
			<xsl:copy-of select="lookupInfo/options" />
		</xsl:element>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.SelectiveResLookupAlgorithm']/properties">
		<xsl:element name="properties">
			<xsl:attribute name="outputColumn"><xsl:value-of select="lookupInfo/outputColumn|lookupInfo/@outputColumn"/></xsl:attribute>
			<xsl:attribute name="useApproximative"><xsl:value-of select="lookupInfo/useApproximative|lookupInfo/@useApproximative"/></xsl:attribute>
			<xsl:attribute name="fileName"><xsl:value-of select="lookupInfo/fileName|lookupInfo/@fileName"/></xsl:attribute>
			<xsl:apply-templates select="*|@*" mode="remove"/>
		</xsl:element>
	</xsl:template>

	<xsl:template match="lookupInfo" mode="remove" />

	<xsl:template match="node()|@*" mode="remove">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="remove"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
