<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="12.1.0" ver:versionTo="12.2.0"
	ver:name="Move ">
	<!-- root data stream -->
	<xsl:template match="step[contains(@className,'com.ataccama.mdu.MdUnify')]">
		<step id="{@id}" className="{@className}" disabled="{@disabled}">
			<properties>
				<xsl:for-each select="properties/@*">
					<xsl:if test="name()!='matchIdColumn' and name()!='ruleNameColumn' and name()!='matchQualityColumn'">
						<xsl:attribute name="{name()}"><xsl:value-of select="."/></xsl:attribute>
					</xsl:if>							
				</xsl:for-each>			
				<xsl:copy-of select="properties/keeperSelectionRule"/>
				<xsl:copy-of select="properties/matchFunctions"/>
				<xsl:copy-of select="properties/matchingMeasures"/>
				<xsl:copy-of select="properties/partitions"/>				
				<xsl:if test="properties/standaloneBindings">
					<standaloneBindings matchRelatedIdColumn="{properties/@matchIdColumn}" matchRuleNameColumn="{properties/@ruleNameColumn}" matchQualityColumn="{properties/@matchQualityColumn}">
						<xsl:for-each select="properties/standaloneBindings/@*">
							<xsl:attribute name="{name()}"><xsl:value-of select="."/></xsl:attribute>					
						</xsl:for-each>						
					</standaloneBindings>
				</xsl:if>
			</properties>				
			<xsl:copy-of select="visual-constraints"/>
		</step>
	</xsl:template>
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>