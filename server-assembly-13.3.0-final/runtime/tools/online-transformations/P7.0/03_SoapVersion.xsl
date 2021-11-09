<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Change the soapVersion constant">

	<xsl:template match="*[@soapVersion]">
		<xsl:copy>
			<xsl:attribute name="soapVersion">
				<xsl:choose>
					<xsl:when test="@soapVersion='1.1'">SOAP11</xsl:when>
					<xsl:when test="@soapVersion='1.2'">SOAP12</xsl:when>
					<xsl:otherwise><xsl:value-of select="@soapVersion"/></xsl:otherwise>
				</xsl:choose>
			</xsl:attribute>
			<xsl:apply-templates select="@*[local-name()!='soapVersion']"/>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>