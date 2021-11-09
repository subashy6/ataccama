<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" exclude-result-prefixes="ver"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.16" ver:versionTo="4.5.17"
	ver:name="Moves 'maxNumberErrors' up to the root of GlobalAddressIdentification">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.GlobalAddressIdentifier']/properties">
		<xsl:variable name='addressEtalon' select='addressEtalon' />
		
		<xsl:copy>
			<xsl:copy-of select='$addressEtalon/@maxNumberErrors' />
			
			<xsl:for-each select="@*">
				<xsl:copy-of select="."/>
			</xsl:for-each>
			<xsl:for-each select="(node())[local-name(.) != 'addressEtalon']">
				<xsl:copy-of select="."/>
			</xsl:for-each>
			
			<xsl:element name='addressEtalon'>
				<xsl:for-each select='$addressEtalon/@*'>
					<xsl:choose>
						<xsl:when test="local-name(.) != 'maxNumberErrors'"><xsl:apply-templates select='.' /></xsl:when>
					</xsl:choose>
				</xsl:for-each>
				<xsl:for-each select='$addressEtalon/node()'>
					<xsl:choose>
						<xsl:when test="local-name(.) != 'maxNumberErrors'"><xsl:apply-templates select='.' /></xsl:when>
					</xsl:choose>
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