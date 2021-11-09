<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Root element rename (cif-config -> purity-config)">
	
	<xsl:template match="/cif-config">
		<purity-config version="4.0.0">
			<xsl:apply-templates/>
		</purity-config>
	</xsl:template>
	

	<!-- The default copy template -->
	<xsl:template match="node()">
		<xsl:copy>
			<xsl:for-each select="@*">
				<xsl:copy />
			</xsl:for-each>
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>