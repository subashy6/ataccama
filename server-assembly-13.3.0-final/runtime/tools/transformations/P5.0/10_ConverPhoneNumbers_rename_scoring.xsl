<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.0" ver:versionTo="5.0.0"
	ver:name="Renames scoring keys *_NONSENCE to *_NONSENSE in ConvertPhoneNumbersAlgorithm">
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.ConvertPhoneNumbersAlgorithm']/properties/scorer/scoringEntries/*">
		<xsl:copy>
			<xsl:apply-templates mode="rencopy" select="key|@key"/>
			<xsl:apply-templates mode="rencopy" select="explainAs|@explainAs"/>
			<xsl:copy-of select="score|@score"/>
			<xsl:copy-of select="explain|@explain"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template mode="rencopy" match="*|@*">
		<xsl:variable name="val" select="."/>
		<xsl:variable name="step" select="ancestor::node()[local-name()='step']"/>
		<xsl:variable name="stepId" select="$step/@id"/>
		<xsl:choose>
			<xsl:when test="substring($val,7) = '_NONSENCE'">
				<xsl:variable name="nval" select="concat(substring($val,1,13),'SE')"/>
				<xsl:attribute name="{name()}"><xsl:value-of select="$nval"/></xsl:attribute>
				<xsl:if test="local-name() = 'explainAs'">
					<xsl:message>Step: <xsl:value-of select="$stepId"/>, scoring entry explainAs parameter '<xsl:value-of select="$val"/>' changed to '<xsl:value-of select="$nval"/>'</xsl:message>
				</xsl:if>
			</xsl:when>
			<xsl:otherwise>
				<xsl:attribute name="{name()}"><xsl:value-of select="$val"/></xsl:attribute>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template name="reportRenamed">
		<xsl:variable name="nodeName" select="local-name()"/>
		<xsl:variable name="origValue" select="." />
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>