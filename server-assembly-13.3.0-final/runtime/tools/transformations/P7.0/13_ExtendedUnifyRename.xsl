<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Renames/moves some properties of ExtendedUnify"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='com.ataccama.dqc.unify.ExtendedUnify']/properties">
		<xsl:copy>
			<xsl:apply-templates select="@*|*" mode="ren"/>
			<xsl:element name="outputStrategy">
				<xsl:attribute name="scope">INDIVIDUAL_RECORDS</xsl:attribute>
				<xsl:attribute name="exportDiscarded"><xsl:value-of select="@exportDiscarded"/></xsl:attribute>
				<xsl:attribute name="exportUnchanged"><xsl:value-of select="'false' = @exportChangedOnly"/></xsl:attribute>
			</xsl:element>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="@exportDiscarded" mode="ren"/>
	<xsl:template match="@exportChangedOnly" mode="ren"/>
	<xsl:template match="operations/*/@clientIdColumn" mode="ren">
		<xsl:attribute name="matchingIdColumn"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="operations/*/@oldClientIdColumn" mode="ren">
		<xsl:attribute name="oldMatchingIdColumn"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="operations/*/@changedFlagColumn" mode="ren">
		<xsl:attribute name="unificationChangeStatusColumn"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="operations/*/@outputLostIds" mode="ren">
		<xsl:attribute name="outputDiscardedIds">
			<xsl:choose>
				<xsl:when test=". = 'true'">BOTH</xsl:when>
				<xsl:otherwise>NONE</xsl:otherwise>
			</xsl:choose>
		</xsl:attribute>
	</xsl:template>
	<xsl:template match="@changedFlagColumn" mode="ren">
		<xsl:attribute name="processingStatusColumn"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@changedTimestampColumn" mode="ren">
		<xsl:attribute name="processingTimestampColumn"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@batchMode" mode="ren">
		<xsl:attribute name="exclusiveMode"><xsl:value-of select="."/></xsl:attribute>
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
