<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="DQI was substituted by DataQualityIndicator step and therefore it was moved to experimental">
	<!--
	DQI bylo presunuto do experimental.
	-->
	<xsl:template match="//@className">
		<xsl:choose>
			<xsl:when test=".=&quot;cz.adastra.cif.tasks.dqi.DQIStep&quot;">
				<xsl:attribute name="className">cz.adastra.cif.tasks.experimental.dqi.DQIStep</xsl:attribute>
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
