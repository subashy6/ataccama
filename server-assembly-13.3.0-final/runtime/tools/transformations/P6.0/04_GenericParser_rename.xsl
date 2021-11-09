<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Renames GenericParserAlgorithm step to PatternParser and updates scoring flag prefixes.">

	<!--
		This transformation replaces 'GenericParserAlgorithm' class-name with the 'PatternParser' one.
		It also checks correctness of the scorer's key names - if there are keys starting with 'GP_'
		prefix then they are replaced with 'PP_' prefixed ones. This check is performed even
		for "new" algorithm-forms (PatternParserAlgorithm|MultiplicativePatternParserAlgorithm) because
		these algorithms can occur with 'GP_' prefixed keys on the scorer "in the wild".
		(originally the name-change and scorer-prefix-change were 2 independent transformations)   
	-->

	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm' or
							  @className='cz.adastra.cif.tasks.parse.MultiplicativePatternParserAlgorithm' or
							  @className='cz.adastra.cif.tasks.parse.PatternParserAlgorithm']/properties/scorer/scoringEntries/*">
		<xsl:apply-templates mode="conv" select="."/>
	</xsl:template>

	<!-- replace "GP_" in key/@key element with "PP_" -->
	<xsl:template mode="conv" match="key[starts-with(.,'GP_')] | @key[starts-with(.,'GP_')]">
		<xsl:attribute name="key"><xsl:value-of select="concat('PP_',substring(.,4))"/></xsl:attribute>
	</xsl:template>
	
	<!-- Above rule does not match - use "just-copy" template for "conv" mode then -->
	<xsl:template mode="conv" match="node()|@*">
		<xsl:copy><xsl:apply-templates mode="conv" select="node()|@*"/></xsl:copy>
	</xsl:template>

	<!-- replace class name template -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm']/@className">
	 	<xsl:attribute name="className">cz.adastra.cif.tasks.parse.PatternParserAlgorithm</xsl:attribute>
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
