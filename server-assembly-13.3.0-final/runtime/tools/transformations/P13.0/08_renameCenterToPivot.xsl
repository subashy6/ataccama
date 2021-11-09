<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="13.2.0" ver:versionTo="13.3.0"
	ver:name="Renames center/slave to pivot/candidate"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.identify.UnifyEngine']/properties">
		<xsl:apply-templates mode="ren" select="."/>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.unify.ExtendedUnify']/properties/operations">
		<xsl:apply-templates mode="ren" select="."/>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.identify.repository.convert.RepositoryKeyConverter']/properties">
		<xsl:apply-templates mode="ren" select="."/>
	</xsl:template>

	<xsl:template mode="ren" match="defaultCenterSelectionRule"><xsl:element name="defaultPivotSelectionRule"><xsl:apply-templates/></xsl:element></xsl:template>
	<xsl:template mode="ren" match="centerSelectionRule"><xsl:element name="pivotSelectionRule"><xsl:apply-templates/></xsl:element></xsl:template>
	<xsl:template mode="ren" match="@useCenterAsSurvivor"><xsl:attribute name="usePivotAsSurvivor"><xsl:value-of select="."/></xsl:attribute></xsl:template>
	<xsl:template mode="ren" match="useCenterAsSurvivor"><xsl:element name="usePivotAsSurvivor"><xsl:value-of select="."/></xsl:element></xsl:template>
	
	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*" mode="ren">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="ren"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>