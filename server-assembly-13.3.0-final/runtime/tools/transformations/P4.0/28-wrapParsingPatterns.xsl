<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: enclose patterns element in patternGroups/patternGroup (GPA, GNSN, VPN)">

	<!--
	    obali patterns do patternGroups/patternGroup
	-->

	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm' or @className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm.java' or @className='cz.adastra.cif.tasks.clean.ValidatePhoneNumberAlgorithm']/properties/parserConfig/patterns">
		<xsl:element name="patternGroups">
			<xsl:element name="patternGroup">
				<xsl:copy-of select="."/>
			</xsl:element>
		</xsl:element>
	</xsl:template>

	<!-- The default copy template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>