<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.4" ver:versionTo="4.5.5"
	ver:name="RegexMatchingAlgorithm: rename value to expression attribute in noMatchColumns">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.RegexMatchingAlgorithm']/properties/noMatchColumns/*/@value">
		<xsl:attribute name="expression">'<xsl:value-of select="."/>'</xsl:attribute>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.RegexMatchingAlgorithm']/properties/noMatchColumns/*/value">
		<xsl:element name="expression">'<xsl:value-of select="."/>'</xsl:element>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.RegexMatchingAlgorithm']/properties/regExpressions/*/resultColumns/*/@value" />

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.RegexMatchingAlgorithm']/properties/regExpressions/*/resultColumns/*/value" />

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>