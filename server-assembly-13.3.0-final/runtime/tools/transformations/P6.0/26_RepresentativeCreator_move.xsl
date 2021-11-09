<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Changes package of RepresentativeCreator">

	<xsl:template match="step/@className[.='cz.adastra.cif.tasks.experimental.bob.RepresentativeCreator']">
		<xsl:attribute name="className">cz.adastra.cif.tasks.identify.bob.RepresentativeCreator</xsl:attribute>
	</xsl:template>

<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
