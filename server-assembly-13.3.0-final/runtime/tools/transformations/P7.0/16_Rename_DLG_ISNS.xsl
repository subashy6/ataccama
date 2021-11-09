<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:comm="http://www.ataccama.com/purity/comment"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Renames Dictionary Lookup Generator do Builder and Intelligent Swap Name Surname to Smart Swap Name Surname."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.addresses.dictionary.DictionaryLookupGenerator']">
		<xsl:copy>
			<xsl:attribute name='className'>com.ataccama.dqc.tasks.addresses.dictionary.DictionaryLookupBuilder</xsl:attribute>
			
			<!-- copy the rest (and not className attribute) -->
			<xsl:apply-templates select="@*[local-name() != 'className']"/>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.clean.IntelligentSwapNameSurnameAlgorithm']">
		<xsl:copy>
			<xsl:attribute name='className'>com.ataccama.dqc.tasks.clean.SmartSwapNameSurnameAlgorithm</xsl:attribute>
			
			<!-- copy the rest (and not className attribute) -->
			<xsl:apply-templates select="@*[local-name() != 'className']"/>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template name="mergeColumns">
		<xsl:param name="gid" />
		<xsl:param name="rdc" />
		
		<xsl:attribute name="recordDescriptorColumn">
			<xsl:value-of select="$gid" /><xsl:value-of select="' '" /><xsl:value-of select="$rdc" />
		</xsl:attribute>
	</xsl:template>
	
</xsl:stylesheet>
