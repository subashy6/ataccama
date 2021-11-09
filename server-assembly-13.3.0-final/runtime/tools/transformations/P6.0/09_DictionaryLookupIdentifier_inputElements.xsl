<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Make components bound to input element of Dictionary lookup identifier single."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/inputLayout/elements/inputElement/components">
		<xsl:choose>
            <xsl:when test="count(entityComponentReference) = 1">
               	<xsl:element name="component">
               		<xsl:value-of select="entityComponentReference/@id" />
				</xsl:element>
            </xsl:when>
            <xsl:otherwise>
            	<xsl:message terminate="yes">You have more than one component bound to an input element. There can only by one.</xsl:message>
            </xsl:otherwise>
		</xsl:choose>
	</xsl:template>
 	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
