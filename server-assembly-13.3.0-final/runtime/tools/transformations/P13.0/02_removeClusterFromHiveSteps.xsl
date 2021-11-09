<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:fn="http://www.w3.org/2005/xpath-functions"
	ver:versionFrom="12.0.0" ver:versionTo="13.0.0"
	ver:name="Remove cluster from Hive Reader and Hive Writer">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.hadoop.io.hcatalog.reader.HCatalogReader']/properties/@cluster"/>

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.hadoop.io.hcatalog.writer.HCatalogWriter']/properties/@cluster"/>
	
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>