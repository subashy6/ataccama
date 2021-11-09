<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: set writeAllColumns='true' if no columns specified (TextFileWriter)">

	<!--
	    nastaveni writeAllColumns pokud neni specifikovan element columns
	-->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.text.write.TextFileWriter']/properties">
		<xsl:copy>
			<xsl:if test="not(columns) and not(writeAllColumns)">
				<xsl:attribute name='writeAllColumns'>true</xsl:attribute>
			</xsl:if>
			<xsl:apply-templates />
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>