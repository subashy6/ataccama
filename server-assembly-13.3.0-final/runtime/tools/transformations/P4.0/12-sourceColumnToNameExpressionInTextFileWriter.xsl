<?xml version="1.0" encoding="UTF-8" ?>

<xsl:stylesheet version="2.0" 
			xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
			xmlns:purity="http://www.ataccama.com/purity"
			xmlns:ver="http://www.ataccama.com/purity/version"
			ver:versionFrom="3.0.0" ver:versionTo="4.0.10"
			ver:name="Rename: 'sourceColumn' to 'name' if 'name' is not specified, otherwise changes 'sourceColumn' to 'expression'">

	<!--
		Prevede sourceColumn v TextFileWriteru a JdbcWriteru na name, pokud uz name neni definovano,
		jinak prevadi sourceColumn na expression a name nechava s puvodnim obsahem
	-->
	
	<xsl:template name="sourceColumn" match="*[sourceColumn or @sourceColumn]
		
		[local-name(parent::node())='columns']
		
		[ancestor::step[contains(@className, 'TextFileWriter') or contains(@className,'JdbcWriter')]]">
	
		<xsl:variable name="name" select="@name|name" />
		<xsl:variable name="sourceColumn" select="@sourceColumn|sourceColumn" />
		
		<xsl:choose>
			<xsl:when test="not($name)">
				<xsl:call-template name="fillNameExpression">
					<xsl:with-param name="name" select="$sourceColumn" />
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$name = $sourceColumn">
				<xsl:call-template name="fillNameExpression">
					<xsl:with-param name="name" select="$sourceColumn" />
				</xsl:call-template>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="fillNameExpression">
					<xsl:with-param name="name" select="$name" />
					<xsl:with-param name="expression" select="$sourceColumn" />
				</xsl:call-template>
			</xsl:otherwise>
		</xsl:choose>
			
	</xsl:template>
	
	<xsl:template name="fillNameExpression">

		<xsl:param name="name" />
		<xsl:param name="expression" />
		
		<xsl:copy>
		
			<xsl:if test="$expression != ''">
				<xsl:attribute name="expression">
					<xsl:value-of select="$expression" />
				</xsl:attribute>
			</xsl:if>
			
			<xsl:attribute name="name">
				<xsl:value-of select="$name" />
			</xsl:attribute>
			
			<xsl:for-each select="(node()|@*)[local-name(.) != 'sourceColumn']">
				<xsl:copy-of select="." />
			</xsl:for-each>
						
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="node()">
		<xsl:copy>
			<xsl:for-each select="@*">
				<xsl:copy /> 
			</xsl:for-each>
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
