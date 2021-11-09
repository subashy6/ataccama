<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.16" ver:versionTo="4.5.17"
	ver:name="Deletion of 'possibleSkipCount' from supporting vector definition element">
	
	<!-- do not copy possibleSkipCount. Either as attribute or as child element -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.GlobalAddressIdentifier']/properties/addressEtalon/supportingVectors/supportingVectorDefinition">
		<xsl:copy>
			<xsl:for-each select="(node()|@*)[local-name(.) != 'possibleSkipCount']">
				<xsl:copy-of select="."/>
			</xsl:for-each>
		</xsl:copy>
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
