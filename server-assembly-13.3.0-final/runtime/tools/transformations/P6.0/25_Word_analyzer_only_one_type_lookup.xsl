<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="With new lookups we have only one type of lookups."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.text.WordAnalyzer']/properties">
	    <xsl:copy>
			    <xsl:apply-templates mode="a" select="node()|@*">
			    </xsl:apply-templates>
		        <xsl:element name="listOfValues">
		           <xsl:for-each select="slListOfValues/slListOfValue">
		               <xsl:element name="listOfValue">
		                   <xsl:attribute name="symbol">
		                      <xsl:value-of select="@symbol"/>
		                   </xsl:attribute>
		                   <xsl:attribute name="fileName">
		                      <xsl:value-of select="@fileName"/>
		                   </xsl:attribute>
		               </xsl:element>
		           </xsl:for-each>
		           <xsl:for-each select="mlListOfValues/mlListOfValue">
		               <xsl:element name="listOfValue">
		                   <xsl:attribute name="symbol">
		                      <xsl:value-of select="@symbol"/>
		                   </xsl:attribute>
		                   <xsl:attribute name="fileName">
		                      <xsl:value-of select="@fileName"/>
		                   </xsl:attribute>
		               </xsl:element>
		           </xsl:for-each>
		        </xsl:element>
	        </xsl:copy>
	</xsl:template>
	
	<xsl:template mode="a" match="slListOfValues|mlListOfValues">
	</xsl:template>
	
	<xsl:template mode="a" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="a" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>