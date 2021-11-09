<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.1.0" ver:versionTo="10.2.0"
	ver:name="Renames I/O attributes of Address Identifier CA"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='com.ataccama.dqc.components.addresses.can.CAAddressesIdentifier']/properties/inEndPoint">
		<xsl:copy>
			<xsl:apply-templates select="@*|*" mode="ren"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="step[@className='com.ataccama.dqc.components.addresses.can.CAAddressesIdentifier']/properties/outEndPoint">
		<xsl:copy>
			<xsl:apply-templates select="@*|*" mode="ren"/>
		</xsl:copy>
	</xsl:template>

	

	<xsl:template match="@inSrc_street" mode="ren">
		<xsl:attribute name="srcAddressLine2"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@inSrc_municipality" mode="ren">
		<xsl:attribute name="srcMunicipality"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@inSrc_province" mode="ren">
		<xsl:attribute name="srcProvinceCode"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@inSrc_postal_code" mode="ren">
		<xsl:attribute name="srcPostalCode"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@inSrc_additional_address_information" mode="ren">
		<xsl:attribute name="srcAddressLine1"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	
	
	<xsl:template match="@outOut_street" mode="ren">
		<xsl:attribute name="outAddressLine2"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@outScore_address" mode="ren">
		<xsl:attribute name="scoAddress"><xsl:value-of select="."/></xsl:attribute>	
	</xsl:template>
	<xsl:template match="@outOut_address_label" mode="ren">
		<xsl:attribute name="addressLabel"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@outOut_postal_code" mode="ren">
		<xsl:attribute name="outPostalCode"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@outCleansing_code" mode="ren">
		<xsl:attribute name="expAddress"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@outOut_province" mode="ren">
		<xsl:attribute name="outProvinceCode"><xsl:value-of select="."/></xsl:attribute>	
	</xsl:template>
	<xsl:template match="@outOut_municipality" mode="ren">
		<xsl:attribute name="outMunicipality"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="@outOut_validation_level" mode="ren">
		<xsl:attribute name="addressValidityLevel"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	
	
	

	<xsl:template match="node()|@*" mode="ren">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"  mode="ren"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	

</xsl:stylesheet>
