<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: type=date to type=day (TextFileReader, DataFormatIntegrator)">
	
	<!--
	    nahrada type=date za type=day v columns a shadowColumns u TextFileReaderu a DataFormatIntegratoru 
		match=<lib. uzel>[majici type][uvnitr columns nebo shadow columns][uvnitr algoritmu TFR nebo DFI]
	-->
	<xsl:template match="*[type or @type]
			[local-name(parent::node())='columns' or local-name(parent::node()) = 'shadowColumns']
			[ancestor::step[contains(@className,'TextFileReader') or contains(@className,'DataFormatChanger')]]">
			
		<xsl:variable name='type' select='@type|type'/>
		<xsl:choose>
			<xsl:when test="$type='date'">
				<xsl:call-template name='createColumn'>
					<xsl:with-param name='type'>day</xsl:with-param>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name='createColumn'/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template name='createColumn'>
		<xsl:param name='type' select='@type|type'/>
		<xsl:copy>
			<xsl:attribute name='type'><xsl:value-of select='$type'/></xsl:attribute>
			<xsl:for-each select="(node()|@*)[local-name(.) != 'type']">
				<xsl:copy-of select="."/>
			</xsl:for-each>
		</xsl:copy> 
	</xsl:template>
	
	<!-- The default copy template -->
	<xsl:template match="node()">
		<xsl:copy>
			<xsl:for-each select="@*">
				<xsl:copy />
			</xsl:for-each>
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>