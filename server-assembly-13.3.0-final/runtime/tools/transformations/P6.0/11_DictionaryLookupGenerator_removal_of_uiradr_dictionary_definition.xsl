<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Translates czech uir-adr dictionary definition into a general one for Dictionary lookup generator."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/etalon[@class='cz.adastra.cif.tasks.addresses.prototype.model.etalon.UirAdrAddressEtalon']/@class">
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/etalon">
		<xsl:element name="dictionaryDefinition">
			<xsl:apply-templates select="node()|@*"/>
		</xsl:element>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
