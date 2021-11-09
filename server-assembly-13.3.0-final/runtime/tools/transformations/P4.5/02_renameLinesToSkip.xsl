<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.3" ver:versionTo="4.5.4"
	ver:name="Replacement: header/footer/LinesToSkip to numberOfLinesInHeader/Footer">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.text.read.TextFileReader']/properties/@linesToSkip">
		<xsl:attribute name="numberOfLinesInHeader"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.text.read.TextFileReader']/properties/linesToSkip">
		<xsl:element name="numberOfLinesInHeader"><xsl:value-of select="."/></xsl:element>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.text.read.FixedWidthFileReader']/properties/@headerLinesToSkip">
		<xsl:attribute name="numberOfLinesInHeader"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.text.read.FixedWidthFileReader']/properties/headerLinesToSkip">
		<xsl:element name="numberOfLinesInHeader"><xsl:value-of select="."/></xsl:element>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.text.read.FixedWidthFileReader']/properties/@footerLinesToSkip">
		<xsl:attribute name="numberOfLinesInFooter"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.text.read.FixedWidthFileReader']/properties/footerLinesToSkip">
		<xsl:element name="numberOfLinesInFooter"><xsl:value-of select="."/></xsl:element>
	</xsl:template>

	<!-- The default copy template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>