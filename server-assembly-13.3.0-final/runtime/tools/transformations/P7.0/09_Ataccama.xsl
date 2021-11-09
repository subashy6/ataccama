<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Step renaming to com.ataccama.dqc">
	<!-- the attribute-aware default template -->

	<xsl:template match="*[@class]">
		<xsl:copy>
			<xsl:attribute name='class'><xsl:choose>
				<xsl:when test='starts-with(@class, "cz.adastra.cif") '>com.ataccama.dqc<xsl:value-of select="substring-after(@class, 'cz.adastra.cif')"/></xsl:when>
				<xsl:when test='starts-with(@class, "com.ataccama.cif") '>com.ataccama.dqc<xsl:value-of select="substring-after(@class, 'com.ataccama.cif')"/></xsl:when>
				<xsl:otherwise><xsl:value-of select="@class"/></xsl:otherwise>
			</xsl:choose></xsl:attribute>
			<xsl:apply-templates select="@*[local-name() != 'class']"/>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="*[@className]">
		<xsl:copy>
			<xsl:attribute name='className'><xsl:choose>
				<xsl:when test='starts-with(@className, "cz.adastra.cif") '>com.ataccama.dqc<xsl:value-of select="substring-after(@className, 'cz.adastra.cif')"/></xsl:when>
				<xsl:when test='starts-with(@className, "com.ataccama.cif") '>com.ataccama.dqc<xsl:value-of select="substring-after(@className, 'com.ataccama.cif')"/></xsl:when>
				<xsl:otherwise><xsl:value-of select="@className"/></xsl:otherwise>
			</xsl:choose></xsl:attribute>
			<xsl:apply-templates select="@*[local-name() != 'className']"/>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
