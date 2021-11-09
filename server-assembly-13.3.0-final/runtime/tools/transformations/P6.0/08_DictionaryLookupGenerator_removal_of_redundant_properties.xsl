<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Removes input property from entity component definition and number component id for Dictionary lookup generator."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/etalon/@numberComponentId">
	</xsl:template>
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/etalon/components/entityComponent/input">
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/etalon/components/entityComponent/@input">
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
