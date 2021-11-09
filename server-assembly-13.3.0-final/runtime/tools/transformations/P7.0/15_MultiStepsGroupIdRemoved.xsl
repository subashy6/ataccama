<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Removes groupId attribute from multiplicative steps"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[
		@className='com.ataccama.dqc.tasks.addresses.dictionary.DictionaryLookupIdentifier'
		or @className='com.ataccama.dqc.tasks.clean.MultiplicativeLookupAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.MultiplicativeAddressDoctorAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.MultiplicativeGuessNameSurnameAlgorithm'
		or @className='com.ataccama.dqc.tasks.parse.MultiplicativePatternParserAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.MultiplicativeRegexMatchingAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.MultiplicativeValidatePhoneNumberAlgorithm'
		or @className='com.ataccama.dqc.tasks.text.Splitter'
		]/properties">
		<xsl:element name="properties">
			<xsl:copy-of select='@*[local-name() != "recordDescriptor" and local-name() != "groupId"]'/>
			<xsl:choose>
				<xsl:when test="string-length(@groupId) &gt; 0 and string-length(@recordDescriptorColumn) &gt; 0">
					<xsl:attribute name="recordDescriptorColumn"><xsl:value-of select="@recordDescriptorColumn"/>/<xsl:value-of select="@groupId"/></xsl:attribute>
				</xsl:when>
				<xsl:when test="string-length(@groupId)">
					<xsl:attribute name="recordDescriptorColumn">/<xsl:value-of select="@groupId"/></xsl:attribute>
				</xsl:when>
				<xsl:when test="string-length(@recordDescriptorColumn) &gt; 0">
					<xsl:attribute name="recordDescriptorColumn"><xsl:value-of select="@recordDescriptorColumn"/></xsl:attribute>
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates />
		</xsl:element>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>