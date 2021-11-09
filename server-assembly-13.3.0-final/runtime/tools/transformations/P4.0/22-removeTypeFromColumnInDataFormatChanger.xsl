<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Removes attribute 'type' from the 'column' of 'DataFormatChanger'">
	
	<!-- remove attribute from the step 'type' -->
	<xsl:template match="step[contains(@className, 'DataFormatChanger')]/properties/*/column/@type"/>
	
	<!-- global copy procesor -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>