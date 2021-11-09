<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.5.6"
	ver:name="Removes matchin value generators from relevant steps">

	<!-- remove bindings from builders -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.MatchingLookupBuilder']/binding[@name='matchingValue']" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.SelectiveMatchingLookupBuilder']/binding[@name='matchingValue']" />

	<!-- rename bindings in builders -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.MatchingLookupBuilder']/binding[@name='realValue']" >
		<xsl:call-template name="ren_bind"><xsl:with-param name="name">key</xsl:with-param></xsl:call-template>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.SelectiveMatchingLookupBuilder']/binding[@name='realValue']" >
		<xsl:call-template name="ren_bind"><xsl:with-param name="name">key</xsl:with-param></xsl:call-template>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.StringLookupBuilder']/binding[@name='indexedValue']" >
		<xsl:call-template name="ren_bind"><xsl:with-param name="name">key</xsl:with-param></xsl:call-template>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.IndexedTableBuilder']/binding[@name='primaryKey']" >
		<xsl:call-template name="ren_bind"><xsl:with-param name="name">key</xsl:with-param></xsl:call-template>
	</xsl:template>

	<!-- converts doRemoveSpecialChars=true to default supportedCharacters -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.CreateMatchingValueAlgorithm']/properties/config/@doRemoveSpecialChars">
		<xsl:call-template name="def_supchars"/>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.CreateMatchingValueAlgorithm']/properties/config/doRemoveSpecialChars">
		<xsl:call-template name="def_supchars"/>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ValidateInResAlgorithm']/properties/matchingNameGeneratorConfig/@doRemoveSpecialChars">
		<xsl:call-template name="def_supchars"/>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ValidateInResAlgorithm']/properties/matchingNameGeneratorConfig/doRemoveSpecialChars">
		<xsl:call-template name="def_supchars"/>
	</xsl:template>

	<xsl:template name="ren_bind">
		<xsl:param name="name"/>
		<xsl:element name="binding">
			<xsl:attribute name="name"><xsl:value-of select="$name"/></xsl:attribute>
			<xsl:attribute name="column"><xsl:value-of select="@column"/></xsl:attribute>
		</xsl:element>
	</xsl:template>

	<xsl:template name="def_supchars">
		<xsl:if test=".='true'">
			<xsl:attribute name="supportedCharacters"> [:letter:][:digit:]</xsl:attribute>
			<xsl:attribute name="substituteWith"> </xsl:attribute>
		</xsl:if>
	</xsl:template>
	
	<!-- removes MVGConfig from several points -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/components/*/verifier/matchingValueConfig" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/matchingValueGenerator" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ValidatePhoneNumberAlgorithm']/properties/components/*/verifier/matchingValueConfig" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm']/properties/parserConfig/components/*/verifier/matchingValueConfig" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.text.WordAnalyzer']/properties/mlListOfValues/*/matchingValueGenerator" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.IntelligentSwapNameSurnameAlgorithm']/properties/matchingValueGenerator" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.SwapNameSurnameAlgorithm']/properties/matchingValueGenerator" />

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>