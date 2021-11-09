<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
                xmlns:ver="http://www.ataccama.com/purity/version"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:fn="http://www.w3.org/2005/xpath-functions"
                ver:versionFrom="13.1.0" ver:versionTo="13.2.0"
                ver:name="Replace scoring/explanation fields in US Address identifier">

    <!-- replacement of score_address with sco_address and cleansing_code with exp_address -->

    <xsl:template match="step[@className='com.ataccama.dqc.components.addresses.us.USAddressesIdentifier']/properties/output/@outScore_address">
        <xsl:attribute name="outSco_address"><xsl:value-of select="."/></xsl:attribute>
    </xsl:template>

    <xsl:template match="step[@className='com.ataccama.dqc.components.addresses.us.USAddressesIdentifier']/properties/output/outScore_address">
        <outSco_address><xsl:value-of select="."/></outSco_address>
    </xsl:template>

    <xsl:template match="step[@className='com.ataccama.dqc.components.addresses.us.USAddressesIdentifier']/properties/output/@outCleansing_code">
        <xsl:attribute name="outExp_address"><xsl:value-of select="."/></xsl:attribute>
    </xsl:template>

    <xsl:template match="step[@className='com.ataccama.dqc.components.addresses.us.USAddressesIdentifier']/properties/output/outCleansing_code">
        <outExp_address><xsl:value-of select="."/></outExp_address>
    </xsl:template>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

</xsl:stylesheet>
