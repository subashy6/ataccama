<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.3.0" ver:versionTo="6.0.0"
	ver:name="Adds TRLR_INVALID and DUMMY_DATE scorings to the RCValidator's scorer.">
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.RCValidatorAlgorithm']/properties/scorer/scoringEntries">
		<xsl:message terminate="no">WARNING: RCValidator logic has changed, please consult RCValidator documentation and review step configuration manually</xsl:message>	
		<xsl:variable name="e_expl" select="scoringEntry[@key='RC_TRLR_INVALID']"/>
		<xsl:variable name="e_dummy" select="scoringEntry[@key='RC_DUMMY_DATE']"/>
		
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
	
			<xsl:choose>
				<xsl:when test="not($e_expl)">
					<xsl:element name="scoringEntry">
						<xsl:attribute name="key">RC_TRLR_INVALID</xsl:attribute>
						<xsl:attribute name="explain">true</xsl:attribute>
					</xsl:element>
				</xsl:when>
			</xsl:choose>
			
			<xsl:choose>
				<xsl:when test="not($e_dummy)">
					<xsl:element name="scoringEntry">
						<xsl:attribute name="key">RC_DUMMY_DATE</xsl:attribute>
						<xsl:attribute name="explain">true</xsl:attribute>
					</xsl:element>
				</xsl:when>
			</xsl:choose>
		</xsl:copy>
	</xsl:template>	
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>