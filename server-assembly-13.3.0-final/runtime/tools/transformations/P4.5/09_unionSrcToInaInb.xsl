<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.0" ver:versionTo="4.5.11"
	ver:name="Replacement: 'src/dest to in_a/in_b/dest in Union'">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.flow.Union']/properties/columnMappings/*">
		<xsl:copy>
			<xsl:variable name='first' select='@dest|dest'/>
			<xsl:variable name='second' select='@src|src'/>

			<xsl:choose>
				<xsl:when test="not ($first)">
					<xsl:attribute name='in_a'><xsl:value-of select='@in_a|in_a'/></xsl:attribute>
				</xsl:when>
				<xsl:otherwise>
					<xsl:attribute name='in_a'><xsl:value-of select='$first'/></xsl:attribute>
				</xsl:otherwise>
			</xsl:choose>

			<xsl:choose>
				<xsl:when test="not ($second)">
					<xsl:attribute name='in_b'><xsl:value-of select='@in_b|in_b'/></xsl:attribute>
				</xsl:when>
				<xsl:otherwise>
					<xsl:attribute name='in_b'><xsl:value-of select='$second'/></xsl:attribute>
				</xsl:otherwise>
			</xsl:choose>

			<xsl:attribute name="dest"><xsl:value-of select="@dest|dest"/></xsl:attribute>

		</xsl:copy>
	</xsl:template>

	<xsl:template match="connection/target">
		<xsl:variable name="id" select="@step|step"/>
		<xsl:choose>
			<xsl:when test="//step[@className='cz.adastra.cif.tasks.flow.Union' and @id=$id]">
				<xsl:variable name="ep" select="@endpoint|endpoint"/>
				<xsl:element name="target">
					<xsl:attribute name="step">
						<xsl:value-of select="@step|step"/>
					</xsl:attribute>
					<xsl:attribute name="endpoint">
						<xsl:choose>
							<xsl:when test="$ep='in'">in_a</xsl:when>
							<xsl:when test="$ep='newIn'">in_b</xsl:when>
						</xsl:choose>
					</xsl:attribute>
				</xsl:element>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
					<xsl:apply-templates select="*|@*"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>