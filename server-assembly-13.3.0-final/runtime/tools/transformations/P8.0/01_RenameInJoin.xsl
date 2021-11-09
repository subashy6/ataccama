<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="7.0.0" ver:versionTo="8.0.0"
	ver:name="Rename properties/endpoints of Join from a/b to left/right">

	<xsl:template match="/purity-config">
		<xsl:copy>
			<xsl:attribute name="version">8.0.0.devel</xsl:attribute>
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="step[@className = 'com.ataccama.dqc.tasks.merge.Join']">
		<xsl:apply-templates select="." mode="conv"/>
	</xsl:template>

	<xsl:template match="connection/target[@endpoint = 'in_a' or @endpoint = 'in_b']">
		<xsl:variable name="step" select="@step"/>
		<xsl:variable name="ep" select="@endpoint"/>
		<xsl:copy>
			<xsl:copy-of select="@step"/>
			<xsl:choose>
				<xsl:when test="//step[@className = 'com.ataccama.dqc.tasks.merge.Join' and @id = $step and $ep = 'in_a']">
					<xsl:attribute name="endpoint">in_left</xsl:attribute>
				</xsl:when>
				<xsl:when test="//step[@className = 'com.ataccama.dqc.tasks.merge.Join' and @id = $step and $ep = 'in_b']">
					<xsl:attribute name="endpoint">in_right</xsl:attribute>
				</xsl:when>
				<xsl:otherwise>
					<xsl:copy-of select="@endpoint"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="@keyA" mode="conv">
		<xsl:attribute name="leftKey"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="keyA" mode="conv">
		<xsl:element name="leftKey"><xsl:value-of select="."/></xsl:element>
	</xsl:template>
	<xsl:template match="@keyB" mode="conv">
		<xsl:attribute name="rightKey"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	<xsl:template match="keyB" mode="conv">
		<xsl:element name="rightKey"><xsl:value-of select="."/></xsl:element>
	</xsl:template>
	<xsl:template match="columnDefinitions/*/@expression" mode="conv">
		<xsl:attribute name="expression">
			<xsl:call-template name="replace">
				<xsl:with-param name="str">
					<xsl:call-template name="replace">
						<xsl:with-param name="str" select="."/>
						<xsl:with-param name="what">in_a.</xsl:with-param>
						<xsl:with-param name="repl">in_left.</xsl:with-param>
					</xsl:call-template>
				</xsl:with-param>
				<xsl:with-param name="what">in_b.</xsl:with-param>
				<xsl:with-param name="repl">in_right.</xsl:with-param>
			</xsl:call-template>
		</xsl:attribute>
	</xsl:template>
	<xsl:template match="columnDefinitions/*/expression" mode="conv">
		<xsl:element name="expression">
			<xsl:call-template name="replace">
				<xsl:with-param name="str">
					<xsl:call-template name="replace">
						<xsl:with-param name="str" select="."/>
						<xsl:with-param name="what">in_a.</xsl:with-param>
						<xsl:with-param name="repl">in_left.</xsl:with-param>
					</xsl:call-template>
				</xsl:with-param>
				<xsl:with-param name="what">in_b.</xsl:with-param>
				<xsl:with-param name="repl">in_right.</xsl:with-param>
			</xsl:call-template>
		</xsl:element>
	</xsl:template>

	<xsl:template match="node()|@*" mode="conv">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="conv"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template name="replace">
		<xsl:param name="str"/>
		<xsl:param name="what"/>
		<xsl:param name="repl"/>
		<xsl:choose>
			<xsl:when test="contains($str, $what)">
				<xsl:value-of select="substring-before($str, $what)"/>
				<xsl:value-of select="$repl"/>
				<xsl:call-template name="replace">
					<xsl:with-param name="str" select="substring-after($str, $what)"/>
					<xsl:with-param name="what" select="$what"/>
					<xsl:with-param name="repl" select="$repl"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$str"/>
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
