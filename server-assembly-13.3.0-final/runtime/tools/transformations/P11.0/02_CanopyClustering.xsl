<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.0.0" ver:versionTo="11.0.0"
	ver:name="Changes output type of Canopy Clustering">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.match.CanopyClustering']/properties">
		<xsl:copy>
			<xsl:apply-templates select="@*|*" mode="ren"/>
		</xsl:copy>
 	</xsl:template>
	
	<xsl:template match="@multiplicative" mode="ren">
		<xsl:attribute name="type">
			<xsl:choose>
		  		<xsl:when test=".='true'">MULTIPLICATIVE</xsl:when>
			  	<xsl:otherwise>UNION</xsl:otherwise>
			</xsl:choose>
		</xsl:attribute>
	</xsl:template>

	<xsl:template match="node()|@*" mode="ren">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="ren"/>
		</xsl:copy>
	</xsl:template>
	
	<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
