<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="9.0.0"
	ver:name="Renames clientId to matchingId properties of unify steps"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.identify.UnifyEngine']/properties/attributes">
		<xsl:copy>
			<xsl:apply-templates select="@*|*" mode="ren"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.identify.repository.write.RepositoryWriter']/properties">
		<xsl:copy>
			<xsl:apply-templates select="@*|*" mode="ren"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="@clientIdColumn" mode="ren">
		<xsl:attribute name="matchingIdColumn"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@oldClientIdColumn" mode="ren">
		<xsl:attribute name="oldMatchingIdColumn"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="clientIdColumn" mode="ren">
		<xsl:element name="matchingIdColumn"><xsl:value-of select="."/></xsl:element>
	</xsl:template>
	<xsl:template match="oldClientIdColumn" mode="ren">
		<xsl:element name="oldMatchingIdColumn"><xsl:value-of select="."/></xsl:element>
	</xsl:template>

	<xsl:template match="node()|@*" mode="ren">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"  mode="ren"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
