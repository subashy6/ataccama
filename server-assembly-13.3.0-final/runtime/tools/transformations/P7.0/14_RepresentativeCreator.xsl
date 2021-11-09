<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:comm="http://www.ataccama.com/purity/comment"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Converts RepresentaticeCreator's grouping strategy"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.identify.bob.RepresentativeCreator']">
		<xsl:apply-templates select="." mode="conv"/>
	</xsl:template>

	<xsl:template match="properties" mode="conv">
		<xsl:copy>
			<xsl:apply-templates select="@*"/>
			<xsl:for-each select="rules/*">
				<xsl:if test="position() = 1">
					<xsl:element name="groupingStrategy">
						<xsl:attribute name="class">com.ataccama.dqc.tasks.common.group.KeyGroupingStrategy</xsl:attribute>
						<xsl:element name="groupBy">
							<xsl:copy-of select="groupBy/*"/>
						</xsl:element>
					</xsl:element>
				</xsl:if>
			</xsl:for-each>
			<xsl:apply-templates select="*" mode="conv"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="properties/rules/*/groupBy" mode="conv">
		<xsl:element name="comm:comment">
Original groupBy key: (<xsl:for-each select="*">
	<xsl:text> </xsl:text><xsl:value-of select="@expression"/><xsl:text> </xsl:text>
</xsl:for-each>)
key of 1st rule has been converted into grouping strategy.
		</xsl:element>
	</xsl:template>

	<xsl:template match="node()|@*" mode="conv">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"  mode="conv"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
