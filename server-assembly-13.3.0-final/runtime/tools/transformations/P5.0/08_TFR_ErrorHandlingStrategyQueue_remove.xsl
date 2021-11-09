<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.8" ver:versionTo="5.0.0"
	ver:name="Removes ErrorHandlingStrategyQueue from TextFileReader (invalid attribute)">

	<!-- remove attribute 'class' from element 'errorHandlingStrategy' located in TextFileReader's
	     properties if it's value is 'cz.adastra.cif.tasks.common.io.error.ErrorHandlingStrategyQueue' -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.text.read.TextFileReader']/properties/errorHandlingStrategy/@class[string()='cz.adastra.cif.tasks.common.io.error.ErrorHandlingStrategyQueue']"/>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>