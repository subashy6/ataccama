<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
                xmlns:ver="http://www.ataccama.com/purity/version"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:fn="http://www.w3.org/2005/xpath-functions"
                ver:versionFrom="13.1.0" ver:versionTo="13.2.0"
                ver:name="Remove components metadata paths"
                exclude-result-prefixes="ver xsl fn">

    <xsl:template match="@fileName">
        <xsl:attribute name="fileName">
            <xsl:value-of select="fn:replace(.,'metadata://(.*)?/components/(.*)?/(.*)?','$3')"/>
        </xsl:attribute>
    </xsl:template>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

</xsl:stylesheet>
