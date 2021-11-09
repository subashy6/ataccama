<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Renames report properties to reports and inputColumn to expression"
	xmlns:java_functions="http://xml.apache.org/xalan/java">
	
	<xsl:template match="step[@className='com.ataccama.cif.reporting.Reporting']/properties/report/report/mapping/mapping/inputColumn | step/properties/reports/report/mapping/mapping/inputColumn">
		<xsl:element name="expression"><xsl:value-of select="." /></xsl:element>
	</xsl:template>

	<xsl:template match="step[@className='com.ataccama.cif.reporting.Reporting']/properties/report/report/mapping/mapping/@inputColumn | step/properties/reports/report/mapping/mapping/@inputColumn">
		<xsl:attribute name="expression"><xsl:value-of select="." /></xsl:attribute>
	</xsl:template>

	<xsl:template match="step[@className='com.ataccama.cif.reporting.Reporting']/properties/report">
		<xsl:element name="reports"><xsl:apply-templates select="node()|@*" /></xsl:element>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>