<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.0" ver:versionTo="5.0.0"
	ver:name="Transformation of Scoring's explanation value.">
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.scoring.ScoringEngineStep']/properties/rules/scoringEngineNode/cases/scoringEngineCase/@explanation">
		<xsl:attribute name="explanation">&quot;<xsl:value-of select="." />&quot;</xsl:attribute>
	</xsl:template>	
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>