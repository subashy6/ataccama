<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.6.1" ver:versionTo="4.6.2"
	ver:name="Removes autocommit property from the JdbcWriter algorithm">
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.jdbc.write.JdbcWriter']/properties/autocommit"/>
	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.jdbc.write.JdbcWriter']/properties/@autocommit"/>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>