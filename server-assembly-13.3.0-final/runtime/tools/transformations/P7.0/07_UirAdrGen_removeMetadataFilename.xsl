<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Removes metadata filename property"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.uiradr.UirAdrGenerator']/properties/metadataFilename">
		<!-- delete the property -->
		<xsl:message terminate="no">Property metadataFilename has been deleted. Please review your plan.</xsl:message>
	</xsl:template>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.uiradr.UirAdrGenerator']/properties/@metadataFilename">
		<!-- delete the property -->
		<xsl:message terminate="no">Property metadataFilename has been deleted. Please review your plan.</xsl:message>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>