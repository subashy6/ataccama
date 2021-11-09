<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.0.0" ver:versionTo="11.0.0"
	ver:name="Changes minRecordCount and maxRecordCount to UniformRecordCountGenerator">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.generator.RandomRecordMultiplicator']/properties">
		<xsl:copy>
  			<xsl:apply-templates select="node()|@*" />

			<xsl:element name="recordCountGenerator">
			  <xsl:attribute name="class">com.ataccama.dqc.tasks.generator.multi.UniformRecordCountGenerator</xsl:attribute>
			  <xsl:attribute name="minRecordCount"> <xsl:value-of select="./@minRecordCount"/></xsl:attribute>
			    <xsl:attribute name="maxRecordCount"> <xsl:value-of select="./@maxRecordCount"/></xsl:attribute>
			</xsl:element>
		</xsl:copy>
 	</xsl:template>

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.generator.RandomRecordMultiplicator']/properties/@minRecordCount"/>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.generator.RandomRecordMultiplicator']/properties/@maxRecordCount"/>


	<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
