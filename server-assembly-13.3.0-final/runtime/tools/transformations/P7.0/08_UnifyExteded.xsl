<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Converts UnifyExtended v6 into ExtendedUnify"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="connection/source/@endpoint">
		<xsl:choose>
			<xsl:when test="contains(., '_out_merged')">
				<xsl:attribute name="endpoint">
					<xsl:value-of select="concat(substring-before(., '_out_merged'), '_merged')"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="step[@className='com.ataccama.incremental.Incremental']">
		<xsl:copy>
			<xsl:attribute name="className">com.ataccama.dqc.unify.ExtendedUnify</xsl:attribute>
			<xsl:apply-templates select="@*[name() != 'className']"/>
			<xsl:apply-templates select="*" mode="ue"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="properties/operations/*" mode="ue">
		<xsl:param name="package">com.ataccama.dqc.unify.config.</xsl:param>
		<xsl:choose>
			<xsl:when test="contains(@class, 'RepresentativeCreatorOperation')">
				<xsl:message terminate="no">groupByColumn of RepresentativeCreatorOperation selected from first rule!</xsl:message>
				<xsl:copy>
					<xsl:attribute name="class"><xsl:value-of select="$package"/>RepresentativeCreatorOperation</xsl:attribute>
					<xsl:attribute name="groupByColumn"><xsl:value-of select="rules/*[position() = 1]/groupBy/keyComponent[position() = 1]/@expression"/></xsl:attribute>
					<xsl:copy-of select="@id"/>
					<xsl:copy-of select="@defaultLocale"/>
					<xsl:apply-templates select="*" mode="ue"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="contains(@class, 'SimpleGroupClassifyOperation')">
				<xsl:copy>
					<xsl:attribute name="class"><xsl:value-of select="$package"/>SimpleGroupClassifyOperation</xsl:attribute>
					<xsl:attribute name="groupByColumn"><xsl:value-of select="@groupIdColumn"/></xsl:attribute>
					<xsl:copy-of select="@id"/>
					<xsl:copy-of select="@roleColumn"/>
					<xsl:copy-of select="columnSets"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="contains(@class, 'AssignOperation')">
				<xsl:copy>
					<xsl:attribute name="class"><xsl:value-of select="$package"/>AssignOperation</xsl:attribute>
					<xsl:copy-of select="@id"/>
					<xsl:copy-of select="assignments"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="contains(@class, 'UnifyOperation')">
				<xsl:copy>
					<xsl:attribute name="class"><xsl:value-of select="$package"/>UnifyOperation</xsl:attribute>
					<xsl:apply-templates select="@*" mode="uni"/>
					<xsl:apply-templates mode="ue"/>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:message terminate="no">Unsupported operation <xsl:value-of select="@class"/> dropped!</xsl:message>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<!-- rename class in unify grouping method -->
	<xsl:template match="groups/*/@class" mode="ue">
		<xsl:attribute name="class">
			<xsl:value-of select="concat('com.ataccama.dqc.tasks.identify.grouping.', substring-after(., 'com.ataccama.incremental.unify.grouping.'))"/>
		</xsl:attribute>
	</xsl:template>

	<!-- copy attributes except class in unify op -->
	<xsl:template match="@class" mode="uni"/>
	<xsl:template match="@*" mode="uni"><xsl:copy/></xsl:template>

	<!-- remove groupBy from BoB -->
	<xsl:template match="rules/*/groupBy" mode="ue"/>

	<!-- copy all in mode ue -->
	<xsl:template match="node()|@*" mode="ue">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="ue"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
