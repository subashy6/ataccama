<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="3.6.2"
	ver:name="Renames 'LookupMatchingAlgorithm' to 'StringLookupAlgorithm'">
	<!--
		Zajistuje prejmenovani algoritmu LookupMatchingAlgorithm na StringLookupAlgorithm

		Tj. meni prislusne atributy obsahujici kompletni cestu ke tride za cestu k nove tride.
	-->

	<xsl:template match="//@className">
		<xsl:choose>
			<!-- DataFormatIntegrator to Union -->
			<xsl:when test=".=&quot;cz.adastra.cif.tasks.clean.LookupMatchingAlgorithm&quot;">
				<xsl:attribute name="className">cz.adastra.cif.tasks.clean.StringLookupAlgorithm</xsl:attribute>
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