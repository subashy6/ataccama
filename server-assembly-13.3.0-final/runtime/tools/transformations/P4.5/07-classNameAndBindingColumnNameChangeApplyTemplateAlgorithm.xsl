<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.5" ver:versionTo="4.5.6"
	ver:name="ApplyTemplateAlgorithm (class name change and column binding change).">

	<!-- class name change -->
	<xsl:template match="//@className">
		<xsl:choose>
			<xsl:when test=".=&quot;cz.adastra.cif.tasks.addresses.ApplyTemplateAlgorithm&quot;">
				<xsl:attribute name="className">cz.adastra.cif.tasks.v1.clean.ApplyTemplateAlgorithm</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:attribute name="className">
					<xsl:value-of select="."/>
				</xsl:attribute>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<!-- binding column name change -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.v1.clean.ApplyTemplateAlgorithm' or 
	@className='cz.adastra.cif.tasks.addresses.ApplyTemplateAlgorithm']//@name[.= 'targetColumn']">
		<xsl:attribute name="name">out</xsl:attribute>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>