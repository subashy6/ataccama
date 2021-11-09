<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: function 'trashDiacritics' to 'removeAccents'">
<!--
	    nahrada funkce trashDiacritics za removeAccents ve vyrazech
-->
	<xsl:template match="expression[contains(.,'trashDiacritics')]">
		<xsl:element name="expression">
			<xsl:call-template name="nahrad">
				<xsl:with-param name="val" select="."/>
			</xsl:call-template>
		</xsl:element>
	</xsl:template>

	<xsl:template match="@expression[contains(.,'trashDiacritics')]">
		<xsl:attribute name="expression">
			<xsl:call-template name="nahrad">
				<xsl:with-param name="val" select="."/>
			</xsl:call-template>
		</xsl:attribute>
	</xsl:template>

	<xsl:template name="nahrad">
		<xsl:param name="val"/>
		<xsl:choose>
			<xsl:when test="contains($val,'trashDiacritics')">
				<xsl:value-of select="concat(substring-before($val,'trashDiacritics'),'removeAccents')"/>
				<xsl:call-template name="nahrad">
					<xsl:with-param name="val" select="substring-after($val,'trashDiacritics')"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$val"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
