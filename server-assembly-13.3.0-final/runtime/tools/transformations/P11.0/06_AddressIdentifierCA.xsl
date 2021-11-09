<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.0.0" ver:versionTo="11.0.0"
	ver:name="Changes certification property and remap status and label columns">

	<xsl:template match="step[@className='com.ataccama.dqc.components.addresses.can.CAAddressesIdentifier']/properties/@certification"/>
	
	<xsl:template match="step[@className='com.ataccama.dqc.components.addresses.can.CAAddressesIdentifier']/properties[@certification='true']/outEndPoint/@addressLabel">
		<xsl:attribute name="addressStatus">
			<xsl:value-of select="."/>
		</xsl:attribute>
	</xsl:template>

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>