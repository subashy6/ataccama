<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Converts verifier type to multiword switch">

	<xsl:template match="components/*">
		<xsl:apply-templates mode="conv" select="."/>
	</xsl:template>

	<xsl:template mode="conv" match="verifier/@type" />
	<xsl:template mode="conv" match="verifier/type" />
	<xsl:template mode="conv" match="verifier/@multiword" />
	<xsl:template mode="conv" match="verifier/multiword" />

	<xsl:template mode="conv" match="@storeInto|storeInto">
		<xsl:attribute name="storeParsedInto"><xsl:value-of select="." /></xsl:attribute>
	</xsl:template>

	<xsl:template mode="conv" match="@storeValidateInto|storeValidateInto">
		<xsl:attribute name="storeValidatedInto"><xsl:value-of select="." /></xsl:attribute>
	</xsl:template>

	<xsl:template match="components/*/scorer/scoringEntries/*">
		<xsl:apply-templates mode="conv" select="."/>
	</xsl:template>

	<xsl:template mode="conv" match="@key[.='GPV_MISMATCH']">
		<xsl:attribute name="key">PPV_MISMATCH</xsl:attribute>
	</xsl:template>

	<xsl:template mode="conv" match="key[.='GPV_MISMATCH']">
		<xsl:element name="key">PPV_MISMATCH</xsl:element>
	</xsl:template>

	<xsl:template mode="conv" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="conv" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>