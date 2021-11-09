<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.1.1" ver:versionTo="5.2.0"
	ver:name="RelationAnalysis - moves left/right keys to one key/component">

	<xsl:template match="//step[@className='cz.adastra.cif.tasks.analysis.relation.RelationAnalysis']">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="pr" />
		</xsl:copy>
	</xsl:template>

	<xsl:template match="properties" mode="pr">
		<xsl:copy>
			<xsl:element name="key">
				<xsl:element name="component">
					<xsl:attribute name="left"><xsl:value-of select="left/@key|left/key"/></xsl:attribute>
					<xsl:attribute name="right"><xsl:value-of select="right/@key|right/key"/></xsl:attribute>
				</xsl:element>
			</xsl:element>
			<xsl:apply-templates select="node()|@*" mode="pr"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="*/@key|*/key" mode="pr"/>

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