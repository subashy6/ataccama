<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: type=date to type=day (Join)">

	<!--
	    nahrada datoveho typu 'date' na 'day' u Join algoritmu
	-->

	<xsl:template match="step[@className='cz.adastra.cif.tasks.merge.VerticalMergeAlgorithm' or @className='cz.adastra.cif.tasks.merge.Join']/properties/columnDefinitions/*/@type[.='date']">
		<xsl:attribute name="type">day</xsl:attribute>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.merge.VerticalMergeAlgorithm' or @className='cz.adastra.cif.tasks.merge.Join']/properties/columnDefinitions/*/type[.='date']">
		<xsl:element name="type">day</xsl:element>
	</xsl:template>

	<!-- The default copy template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>