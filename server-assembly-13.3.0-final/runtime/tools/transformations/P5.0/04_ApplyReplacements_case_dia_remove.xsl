<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.0" ver:versionTo="5.0.0"
	ver:name="Removes caseInsensitive and diaInsensitive attributes from ApplyAttributes and ValueReplacer">
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ApplyReplacementsAlgorithm' or
							  @className='cz.adastra.cif.tasks.clean.ValueReplacer']/properties/@caseInsensitive">
		<xsl:call-template name="reportRemoved"/>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ApplyReplacementsAlgorithm' or
							  @className='cz.adastra.cif.tasks.clean.ValueReplacer']/properties/caseInsensitive">
		<xsl:call-template name="reportRemoved"/>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ApplyReplacementsAlgorithm' or
							  @className='cz.adastra.cif.tasks.clean.ValueReplacer']/properties/@diaInsensitive">
		<xsl:call-template name="reportRemoved"/>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ApplyReplacementsAlgorithm' or
							  @className='cz.adastra.cif.tasks.clean.ValueReplacer']/properties/diaInsensitive">
		<xsl:call-template name="reportRemoved"/>
	</xsl:template>
	
	<xsl:template name="reportRemoved">
		<xsl:variable name="nodeName" select="local-name()"/>
		<xsl:variable name="origValue" select="." />
		<xsl:variable name="step" select="ancestor::node()[local-name()='step']"/>
		<xsl:variable name="stepId" select="$step/@id"/>
		<xsl:message>Step: <xsl:value-of select="$stepId"/>, attribute: <xsl:value-of select="$nodeName"/>='<xsl:value-of select='$origValue'/>' removed!</xsl:message>
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>