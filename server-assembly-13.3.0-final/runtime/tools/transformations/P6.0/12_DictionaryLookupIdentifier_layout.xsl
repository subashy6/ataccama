<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Convert input layout for Dictionary lookup identifier."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/inputLayouts">
		<xsl:variable name="countInputLayouts" select="count(inputLayout)" />
		<xsl:choose>
            <xsl:when test="count(inputLayout) = 1">
               	<xsl:apply-templates select="inputLayout"/>
            </xsl:when>
            <xsl:otherwise>
            	<xsl:message terminate="yes">You have more than one layout used in your plan, thus it cannot be converted and you have to convert it manually.</xsl:message>
            </xsl:otherwise>
		</xsl:choose>

	</xsl:template>
	
	<xsl:template match="inputLayout">
		<xsl:apply-templates select="node()|@*"/>	
	</xsl:template>
	
	<xsl:template match="inputLayout/elements">
		<xsl:element name="inputLayout">
			<xsl:element name="elements">
				<xsl:apply-templates select="node()|@*" />
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="inputLayout/layout">
		<xsl:call-template name="createLayout">
			<xsl:with-param name="layout" select="." />
		</xsl:call-template>
	</xsl:template>
	
	<xsl:template match="inputLayout/@layout">
		<xsl:call-template name="createLayout">
			<xsl:with-param name="layout" select="." />
		</xsl:call-template>
	</xsl:template>
	
	<xsl:template name="createLayout">
		<xsl:param name="layout" />
		<xsl:element name="inputLayout">
			<xsl:element name="elements">
				<xsl:element name="inputElement">
					<xsl:attribute name="name">all</xsl:attribute>
					<xsl:element name="expression">
						<xsl:value-of select="$layout" />
					</xsl:element>
				</xsl:element>
			</xsl:element>
		</xsl:element>
 	</xsl:template>
 	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
