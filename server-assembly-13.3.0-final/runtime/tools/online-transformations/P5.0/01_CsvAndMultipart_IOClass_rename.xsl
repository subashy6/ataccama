<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="5.1.1"
	ver:name="Renames generic CSV and Multipart formats to specialized Input/Output ones">
	
	<xsl:template name="processCsvFormat">
		<xsl:copy>
			<xsl:choose>
				<xsl:when test="ancestor::node()[local-name()='input']">
					<xsl:attribute name="class">cz.adastra.cif.online.config.CsvInputFormat</xsl:attribute> 
				</xsl:when>
				<xsl:otherwise>
					<xsl:attribute name="class">cz.adastra.cif.online.config.CsvOutputFormat</xsl:attribute>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>	
	</xsl:template>
	
	<xsl:template name="processMultiFormat">
		<xsl:copy>
			<xsl:choose>
				<xsl:when test="ancestor::node()[local-name()='input']">
					<xsl:attribute name="class">cz.adastra.cif.online.config.MultipartInputFormat</xsl:attribute> 
				</xsl:when>
				<xsl:otherwise>
					<xsl:attribute name="class">cz.adastra.cif.online.config.MultipartOutputFormat</xsl:attribute>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:apply-templates select="node()|@*"/>		
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="format[@class='cz.adastra.cif.online.config.CsvFormat']">
		<xsl:call-template name="processCsvFormat"/>
	</xsl:template>
	
	<xsl:template match="iFormat[@class='cz.adastra.cif.online.config.CsvFormat']">
		<xsl:call-template name="processCsvFormat"/>
	</xsl:template>
	
	<xsl:template match="format[@class='cz.adastra.cif.online.config.MultipartFormat']">
		<xsl:call-template name="processMultiFormat"/>
	</xsl:template>

	<xsl:template match="iFormat[@class='cz.adastra.cif.online.config.MultipartFormat']">
		<xsl:call-template name="processMultiFormat"/>
	</xsl:template>
	
	<!-- skip copying CsvFormat and MultipartFormat class attributes -->
	<xsl:template match="format[@class='cz.adastra.cif.online.config.CsvFormat']/@class"/>
	<xsl:template match="iFormat[@class='cz.adastra.cif.online.config.CsvFormat']/@class"/>
	<xsl:template match="format[@class='cz.adastra.cif.online.config.MultipartFormat']/@class"/>
	<xsl:template match="iFormat[@class='cz.adastra.cif.online.config.MultipartFormat']/@class"/>
		
	<!-- remove maximalLength attribute on output type of CsvFormat --> 
	<xsl:template match="format[@class='cz.adastra.cif.online.config.CsvFormat' and ancestor::node()[local-name()='outputMethod']]/@maximalLength"/>
	<xsl:template match="iFormat[@class='cz.adastra.cif.online.config.CsvFormat' and ancestor::node()[local-name()='outputMethod']]/@maximalLength"/>
	 
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>