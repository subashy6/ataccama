<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.0" ver:versionTo="4.5.0"
	ver:name="CharacterGroupsAnalyzer: rename characterGroups to defaultCharacterGroups">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.text.CharacterGroupsAnalyzer']/properties/characterGroups">
		<xsl:element name="defaultCharacterGroups"><xsl:apply-templates /></xsl:element>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>