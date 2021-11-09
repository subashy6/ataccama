<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.0" ver:versionTo="4.6.0"
	ver:name="Converting comma separated column lists in SimpleGroupClassifier into regular array elements">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.groupClassification.SimpleGroupClassifier']/properties/unificationRoleColumn"/>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.groupClassification.SimpleGroupClassifier']/properties/@unificationRoleColumn"/>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.identify.groupClassification.SimpleGroupClassifier']/properties/columnSets/*">
		<xsl:copy>
			<xsl:apply-templates select="*|@*" mode="convert" />
		</xsl:copy>
	</xsl:template>

	<xsl:template match="columns|@columns|importantColumns|@importantColumns|fuzzyColumns|@fuzzyColumns" mode="convert">
		<xsl:element name="{local-name()}">
			<xsl:call-template name="gener">
				<xsl:with-param name="val" select="."/>
			</xsl:call-template>
		</xsl:element>
	</xsl:template>

	<xsl:template match="node()|@*" mode="convert">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template name="gener">
		<xsl:param name="val"/>
		<xsl:choose>
			<xsl:when test="contains($val,',')">
				<xsl:call-template name="gener1">
					<xsl:with-param name="val" select="substring-before($val, ',')"/>
				</xsl:call-template>
				<xsl:call-template name="gener">
					<xsl:with-param name="val" select="substring-after($val, ',')"/>
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="gener1">
					<xsl:with-param name="val" select="$val"/>
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template name="gener1">
		<xsl:param name="val"/>
		<xsl:if test="normalize-space($val)">
			<xsl:element name="item">
				<xsl:attribute name="name"><xsl:value-of select="$val"/></xsl:attribute>
			</xsl:element>
		</xsl:if>
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
