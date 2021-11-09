<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:fn="http://www.w3.org/2005/xpath-functions"
	ver:versionFrom="13.0.0" ver:versionTo="13.1.0"
	ver:name="Remove writeAllColumns flag from One Metadata Writer">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.io.mmm.writer.MMMWriter']/properties/@writeAllColumns"/>
	
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>