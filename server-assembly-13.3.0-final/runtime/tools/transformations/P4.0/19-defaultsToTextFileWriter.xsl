<?xml version="1.0" encoding="UTF-8" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
				xmlns:ver="http://www.ataccama.com/purity/version"
				ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
				ver:name="Creates global 'DataFormatParameters' for TextFileWriter if not present">
	
	<!--
	
		Pokud nejsou u TextFileWriteru definovany globalni DataFormatParameters,
		vytvori je a nasetuje je s vychozim nastavenim pro DataFormatParameters, tj.:
		
		trueValue			true
		falseValu			false
		dateFormatLocale	en_US
		dateTimeFormat		yyyy-MM-dd HH:mm:ss
		dayFormat			yyyy-MM-dd
		decimalSeparator	.
		thousandsSeparator	,
		
	-->
	
	<xsl:template name="defaults" match="step[contains(@className, 'TextFileWriter')]/properties">

		<xsl:variable name="dataFormats" select="dataFormatParameters" />
		<xsl:variable name="errorHandling" select="errorHandlingStrategy" />
			
		<xsl:copy>
			<xsl:if test="not($dataFormats)">
				<xsl:element name="dataFormatParameters" >
					<xsl:attribute name="trueValue">true</xsl:attribute>
					<xsl:attribute name="falseValue">false</xsl:attribute>
					<xsl:attribute name="dateFormatLocale">en_US</xsl:attribute>
					<xsl:attribute name="dateTimeFormat">yyyy-MM-dd HH:mm:ss</xsl:attribute>
					<xsl:attribute name="decimalSeparator">.</xsl:attribute>
					<xsl:attribute name="thousandsSeparator">,</xsl:attribute>
					<xsl:attribute name="dayFormat">yyyy-MM-dd</xsl:attribute>
				</xsl:element>
			</xsl:if>
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="node()">
		<xsl:copy>
			<xsl:for-each select="@*">
				<xsl:copy /> 
			</xsl:for-each>
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
