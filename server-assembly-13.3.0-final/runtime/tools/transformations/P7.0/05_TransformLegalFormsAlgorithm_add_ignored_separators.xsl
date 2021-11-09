<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Removes specialsSensitive parameter and adds default tokenizer for Transform Legal Forms">

	<!-- remove specialsSensitive parameter -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.TransformLegalFormsAlgorithm']/properties/@specialsSensitive">
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.TransformLegalFormsAlgorithm']/properties/specialsSensitive">
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.TransformLegalFormsAlgorithm']/properties">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
			<xsl:variable name="specialsSensitiveAttr" select="@specialsSensitive" /> 
			<xsl:variable name="specialsSensitiveElem" select="specialsSensitive" />
			
			<xsl:choose>
				<xsl:when test="$specialsSensitiveAttr = 'false'">
					<xsl:call-template name="createIgnoredSeparators" />
				</xsl:when>
				<xsl:when test="$specialsSensitiveElem = 'false'">
					<xsl:call-template name="createIgnoredSeparators" />
				</xsl:when>
				<xsl:when test="not($specialsSensitiveElem) and not($specialsSensitiveAttr)">
					<xsl:call-template name="createIgnoredSeparators" />
				</xsl:when>
			</xsl:choose>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template name="createIgnoredSeparators">
		<xsl:attribute name="ignoredSeparators">._/</xsl:attribute>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>