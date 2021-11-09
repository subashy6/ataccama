<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.0" ver:versionTo="4.5.15"
	ver:name="Deletion of component's cleaner in GNSN, GPA and VPN">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ValidatePhoneNumberAlgorithm']/properties/components/*/cleaner"/>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/components/*/cleaner"/>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm']/properties/components/*/cleaner"/>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
