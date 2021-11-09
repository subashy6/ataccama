<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Moves Profiling's maskName from frequencyAnalysis to profiledData level, removes profiledData.name">
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']/properties">
		<xsl:apply-templates mode="conv" select="."/>
	</xsl:template>

	<xsl:template mode="conv" match="*[frequencyAnalysis/@maskName]">
		<xsl:copy>
			<xsl:attribute name="maskName"><xsl:value-of select="frequencyAnalysis/@maskName"/></xsl:attribute>
			<xsl:apply-templates mode="conv" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template mode="conv" match="@maskName"/>

	<xsl:template mode="conv" match="dataToProfile/*/name"/>
	<xsl:template mode="conv" match="dataToProfile/*/@name"/>

	<xsl:template mode="conv" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="conv" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>