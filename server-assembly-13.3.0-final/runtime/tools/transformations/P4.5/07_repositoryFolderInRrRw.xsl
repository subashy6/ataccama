<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.5" ver:versionTo="4.5.6"
	ver:name="Converts repositoryFolder to repository.folder in Repository reader/writer">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.repository.read.RepositoryReader']/properties">
		<xsl:element name="properties">
			<xsl:apply-templates mode="RF" select="*|@*"/>
		</xsl:element>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.repository.write.RepositoryWriter']/properties">
		<xsl:element name="properties">
			<xsl:apply-templates mode="RF" select="*|@*"/>
		</xsl:element>
	</xsl:template>

	<xsl:template mode="RF" match="repositoryFolder|@repositoryFolder">
		<xsl:element name="repository">
			<xsl:attribute name="folder"><xsl:value-of select="."/></xsl:attribute>
		</xsl:element>
	</xsl:template>

	<xsl:template mode="RF" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="RF" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>