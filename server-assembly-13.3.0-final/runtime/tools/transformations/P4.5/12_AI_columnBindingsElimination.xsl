<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" exclude-result-prefixes="ver"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.10" ver:versionTo="4.5.11"
	ver:name="ColumnBinding elimination/reorganization for AddressIdentifier">

	<xsl:variable name="settings">
		errors
		errorExplanation
		parserRuleName
		hasStreets
		trashed
	</xsl:variable>
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.AddressIdentifier']/properties">
		<xsl:variable name='outputComponents' select='outputComponents' />
		
		<xsl:copy>
			<xsl:for-each select="@*">
				<xsl:copy-of select="."/>
			</xsl:for-each>
			<xsl:for-each select="(node())[local-name(.) != 'outputComponents']">
				<xsl:copy-of select="."/>
			</xsl:for-each>
		
			
			<xsl:for-each select='$outputComponents/node()'>
				<xsl:choose>
					<xsl:when test="contains($settings, local-name(.))"><xsl:apply-templates select='.' /></xsl:when>
				</xsl:choose>
				<!-- rest ignored -->
			</xsl:for-each>
			
			<xsl:element name='outputComponents'>
				<xsl:for-each select='$outputComponents/node()'>
				<xsl:choose>
					<xsl:when test="not(contains($settings, local-name(.)))"><xsl:apply-templates select='.' /></xsl:when>
				</xsl:choose>
				<!-- rest ignored -->
			</xsl:for-each>
			</xsl:element>
		
		</xsl:copy>
	</xsl:template>

	<!-- The default copy template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>