<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Setting section and column strategies"
	exclude-result-prefixes="ver">
	
	<xsl:template name="create_multiple_section">
		<xsl:variable name="sectionName">
			<xsl:choose>
				<xsl:when test="columns/*/@nodeName"><xsl:value-of select="columns/*/@nodeName"/></xsl:when>
				<xsl:otherwise><xsl:value-of select="columns/*/@name"/></xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<section strategy="MULTIPLE_OPTIONAL">
			<xsl:attribute name="name"><xsl:value-of select="$sectionName"/></xsl:attribute>
			<xsl:attribute name="stepId"><xsl:value-of select="@stepId"/></xsl:attribute>
			<columns>
				<xsl:apply-templates select="columns/xmlColumn"/>
			</columns>
			<xsl:if test="../../@multiple='true'">
				<foreignColumns>
					<column name="fkId" column="pkId">
						<xsl:attribute name="stepId"><xsl:value-of select="../../@stepId"/></xsl:attribute>
					</column>
				</foreignColumns>
			</xsl:if>
		</section>
	</xsl:template>
	
	<xsl:template match="*[columns/*/@multiple='true']">
		<xsl:copy>
			<xsl:apply-templates select="@name"/>
			<xsl:apply-templates select="@stepId"/>
			<xsl:if test="local-name()!='rootSection'">
				<xsl:attribute name="strategy">
					<xsl:choose>
						<xsl:when test="@multiple='true'">MULTIPLE_OPTIONAL</xsl:when>
						<xsl:otherwise>SINGLE_REQUIRED</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>
			</xsl:if>
			<sections>
				<xsl:call-template name="create_multiple_section"/>
				<xsl:apply-templates select="sections/*"/>
			</sections>
			<xsl:apply-templates select="foreignColumns"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="xmlColumn">
		<xsl:copy>
			<xsl:attribute name="strategy">
				<xsl:choose>
					<xsl:when test="@multiple='true' and not(@attribute='true')">TEXT_NODE</xsl:when>
					<xsl:when test="not(@multiple='true') and not(@attribute='true')">NILLABLE</xsl:when>
					<xsl:when test="not(@multiple='true') and @attribute='true'">ATTRIBUTE</xsl:when>
					<xsl:when test="not(@multiple='true') and @nodeType='element'">NILLABLE</xsl:when>
					<xsl:when test="not(@multiple='true') and @nodeType='attribute'">ATTRIBUTE</xsl:when>
				</xsl:choose>
			</xsl:attribute>
			<xsl:apply-templates select="@*[local-name()!='multiple' and local-name()!='attribute']"/>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="section|xmlSection|rootSection">
		<xsl:copy>
			<xsl:if test="local-name()!='rootSection'">
				<xsl:attribute name="strategy">
					<xsl:choose>
						<xsl:when test="@multiple='true'">MULTIPLE_OPTIONAL</xsl:when>
						<xsl:otherwise>SINGLE_REQUIRED</xsl:otherwise>
					</xsl:choose>
				</xsl:attribute>
			</xsl:if>
			<xsl:apply-templates select="@*[local-name()!='multiple']"/>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>