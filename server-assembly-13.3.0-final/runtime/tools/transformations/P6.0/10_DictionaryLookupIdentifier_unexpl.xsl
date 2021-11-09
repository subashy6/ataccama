<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Replace pa.unexpl column with unexpl.all of Dictionary lookup identifier."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<!-- scoring.when -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/scoring/scoring/@when">
		<xsl:attribute name="when"><xsl:call-template name="replace-unexpl" /></xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/scoring/scoring/when">
		<xsl:element name="when"><xsl:call-template name="replace-unexpl" /></xsl:element>
	</xsl:template>
 	
	<!-- scoring.explanation -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/scoring/scoring/@explanation">
		<xsl:attribute name="explanation"><xsl:call-template name="replace-unexpl" /></xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/scoring/scoring/explanation">
		<xsl:element name="explanation"><xsl:call-template name="replace-unexpl" /></xsl:element>
	</xsl:template>
 
	<!-- rating.when -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/rating/rating/@when">
		<xsl:attribute name="when"><xsl:call-template name="replace-unexpl" /></xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/rating/rating/when">
		<xsl:element name="when"><xsl:call-template name="replace-unexpl" /></xsl:element>
	</xsl:template>
	
	<!-- rating.rate -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/rating/rating/@rate">
		<xsl:attribute name="rate"><xsl:call-template name="replace-unexpl" /></xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/rating/rating/rate">
		<xsl:element name="rate"><xsl:call-template name="replace-unexpl" /></xsl:element>
	</xsl:template>
 	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
	<!-- internal "functions" -->
	<xsl:template name="replace-unexpl">
		<xsl:variable name="long_unexpl"><xsl:call-template name="replace-unexpl-step">
				<xsl:with-param name="text" select="." />
			</xsl:call-template></xsl:variable>
		
		<xsl:call-template name="replace-unexpl-step">
			<xsl:with-param name="text" select="$long_unexpl" />
		</xsl:call-template>
	</xsl:template>

	<xsl:template name="replace-unexpl-step">
		<xsl:param name="text"/>
	    <xsl:choose>
	    	<xsl:when test="contains($text, 'pa.unexpl_')">
	    		<xsl:call-template name="replace-string">
					<xsl:with-param name="str" select="$text" />
					<xsl:with-param name="what" select="'pa.unexpl_'" />
					<xsl:with-param name="with" select="'unexpl.'" />
				</xsl:call-template>
	    	</xsl:when>
			<xsl:when test="contains($text, 'pa.unexpl')">
				<xsl:call-template name="replace-string">
					<xsl:with-param name="str" select="$text" />
					<xsl:with-param name="what" select="'pa.unexpl'" />
					<xsl:with-param name="with" select="'unexpl.total'" />
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$text"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template name="replace-string">
		<xsl:param name="str" />
		<xsl:param name="what" />
		<xsl:param name="with" />
		<xsl:choose>
			<xsl:when test="contains($str,$what)">
				<xsl:value-of select="substring-before($str,$what)" />
				<xsl:value-of select="$with" />
				<xsl:call-template name="replace-string">
					<xsl:with-param name="str" select="substring-after($str,$what)" />
					<xsl:with-param name="what" select="$what" />
					<xsl:with-param name="with" select="$with" />
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$str" />
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	
</xsl:stylesheet>
