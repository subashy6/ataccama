<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Removes obsolete properties from Dictionary Lookup Generator">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/componentWordDefinition"/>
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/@congruent" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/congruent" />
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/@commonName" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/commonName" />
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/@approximative">
		<xsl:message terminate="no">Make sure you set approximation related properties on the matching component usage in Dictionary Lookup Identifier</xsl:message>
	</xsl:template> 
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/approximative">
		<xsl:message terminate="no">Make sure you set approximation related properties on the matching component usage in Dictionary Lookup Identifier</xsl:message>
	</xsl:template> 
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/@containsNumbers" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/containsNumbers" />

<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>