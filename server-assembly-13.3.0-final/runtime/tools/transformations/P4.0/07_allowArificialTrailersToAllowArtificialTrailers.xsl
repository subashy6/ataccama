<?xml version="1.0" encoding="UTF-8" ?>

<xsl:stylesheet version="2.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: 'allowArificialTrailers' to 'allowArtificialTrailers'">

    <!--
        nahrada allowArificialTrailers za allowArtificialTrailers v elementech
        (chybi t)      ^ 
    -->
	
    <xsl:template match="properties/allowArificialTrailers">
        <allowArtificialTrailers><xsl:value-of select="."/></allowArtificialTrailers>
    </xsl:template>

    <!-- the attribute-aware default template -->
    <xsl:template match="node()|@*">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>
   
</xsl:stylesheet>
