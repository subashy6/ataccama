<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Moves profiling's FkAnalysis to top level"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.profiling.ProfilingAlgorithm']">
		<xsl:choose>
			<xsl:when test="properties/inputs/*/fkAnalysis/*">
				<xsl:apply-templates mode="convfk" select="."/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates mode="conv" select="."/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template mode="convfk" match="properties">
		<xsl:copy>
			<xsl:apply-templates mode="conv" select="node()|@*"/>
			<xsl:element name="fkAnalysis">
				<xsl:for-each select="inputs/*/fkAnalysis/*">
					<xsl:element name="fkAnalysis">
						<xsl:attribute name="name"><xsl:value-of select="@name|name"/></xsl:attribute>
						<xsl:attribute name="leftInputName"><xsl:value-of select="../../@name|../../name"/></xsl:attribute>
						<xsl:attribute name="rightInputName"><xsl:value-of select="@parentInputName|parentInputName"/></xsl:attribute>
						<xsl:element name="components">
							<xsl:apply-templates mode="convfk"/>
						</xsl:element>
					</xsl:element>
				</xsl:for-each>
			</xsl:element>
		</xsl:copy>
	</xsl:template>

	<xsl:template mode="convfk" match="components/*">
		<xsl:copy>
			<xsl:attribute name="leftColumn"><xsl:value-of select="@localColumn|localColumn"/></xsl:attribute>
			<xsl:attribute name="rightColumn"><xsl:value-of select="@parentColumn|parentColumn"/></xsl:attribute>
		</xsl:copy>
	</xsl:template>

	<xsl:template mode="conv" match="properties/inputs/*/fkAnalysis"/>

	<xsl:template mode="conv" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="conv" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
