<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:comm="http://www.ataccama.com/purity/comment"
	ver:versionFrom="5.2.0" ver:versionTo="5.3.0"
	ver:name="Replacement: function 'levenstein' to 'levenshtein'">

	<!-- search levenstein( in expression -->
	<xsl:template match="properties//*[not(*) and contains(text(),'levenstein(')]">
		<xsl:element name="{name()}">
			<xsl:apply-templates select="@*"/>
			<xsl:call-template name="nahrad">
				<xsl:with-param name="val" select="."/>
			</xsl:call-template>
		</xsl:element>
	</xsl:template>

	<xsl:template match="properties//@*[contains(.,'levenstein(')]">
		<xsl:attribute name="{name()}">
			<xsl:call-template name="nahrad">
				<xsl:with-param name="val" select="."/>
			</xsl:call-template>
		</xsl:attribute>
	</xsl:template>

	<!-- levenstein in matching rules/tests/function -->
	<xsl:template match="properties//matchingRules/*/tests/*/function[. = 'levenstein']">
		<xsl:element name="function">levenshtein</xsl:element>
	</xsl:template>

	<xsl:template match="properties//matchingRules/*/tests/*/@function[. = 'levenstein']">
		<xsl:attribute name="function">levenshtein</xsl:attribute>
	</xsl:template>

	<xsl:template name="nahrad">
		<xsl:param name="val"/>
		<xsl:choose>
			<xsl:when test="contains($val,'levenstein(')">
				<xsl:value-of select="concat(substring-before($val,'levenstein('),'levenshtein(')"/>
				<xsl:call-template name="nahrad">
					<xsl:with-param name="val" select="substring-after($val,'levenstein(')"/>
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
