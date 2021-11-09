<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="7.0.0" ver:versionTo="8.0.0"
	ver:name="Removes deprecated scoring entries from Web Lookup">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.io.html.WebLookupAlgorithm']/properties/scorer/scoringEntries/scoringEntry[@key='WLA_UNABLE_TO_TRANSFORM_RESPONSE_TO_XML']">
        <!-- delete this key -->
    </xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
