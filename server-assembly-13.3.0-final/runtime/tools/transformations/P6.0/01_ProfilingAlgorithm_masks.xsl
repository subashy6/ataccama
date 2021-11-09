<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Converts Profiling's mask character groups to default mask definition item">
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']/properties">
		<xsl:apply-templates mode="conv" select="."/>
	</xsl:template>

	<xsl:template mode="conv" match="dataToProfile/*/frequencyAnalysis/@mask">
		<xsl:if test=".='true'">
			<xsl:attribute name="maskName">default</xsl:attribute>
		</xsl:if>
	</xsl:template>
	<xsl:template mode="conv" match="dataToProfile/*/groupSizeAnalysis/@mask"/>

	<xsl:template mode="conv" match="maskCharacterGroups">
		<xsl:if test="*">
			<xsl:element name="masks">
				<xsl:element name="maskCfg">
					<xsl:attribute name="name">default</xsl:attribute>
					<xsl:if test="../@maskCopyOther">
						<xsl:attribute name="copyOther"><xsl:value-of select="../@maskCopyOther"/></xsl:attribute>
					</xsl:if>
					<xsl:element name="characterGroups">
						<xsl:copy-of select="*"/>
					</xsl:element>
				</xsl:element>
			</xsl:element>
		</xsl:if>
	</xsl:template>

	<xsl:template mode="conv" match="@maskCopyOther"/>		

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