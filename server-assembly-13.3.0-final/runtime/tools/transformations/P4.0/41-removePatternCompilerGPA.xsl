<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.14"
	ver:name="Remove: 'patternCompiler' (GenericParserAlgorithm)">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm']/properties/patternCompiler" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm']/properties/@patternCompiler" />

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>