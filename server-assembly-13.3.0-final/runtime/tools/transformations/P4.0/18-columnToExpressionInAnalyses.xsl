<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Renames 'column' to 'expression' for analytic algorithms">

	<!-- 
		Prejmenovava atribut 'column' na atribut 'expression'. Deje se tak u elementu 'analysis' v
		kroku FrequencyAnalysisAlgorithm a elementu 'statistic' algoritmu StatisticsAlgorithm
	 -->
	
	<!-- for statistic and analysis nodes in StatisticAlgorithm/FrequencyAnalysisAlgorithm
		 replace possible 'column' definition with 'expression' one 
		 (in elements and attributes) -->
		 
	<xsl:template match="node()[name()='statistic' or name()='analysis']
	 	[ ancestor::step[contains(@className,'StatisticsAlgorithm')] or
	 	  ancestor::step[contains(@className,'FrequencyAnalysisAlgorithm')] ]">
	 	<xsl:variable name="tagName" select="name()"/>
		<xsl:element name="{$tagName}">
			<xsl:for-each select="@*">
				<xsl:choose>
					<xsl:when test="name()='column'">
						<xsl:attribute name='expression'><xsl:value-of select="."/></xsl:attribute>					
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>	
			
			<xsl:for-each select="node()">
				<xsl:choose>
					<xsl:when test="name()='column'">
						<xsl:element name='expression'>
							<xsl:copy-of select="node()"/>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
	 	</xsl:element>
	</xsl:template>
	
 
	<!-- global copy procesor -->
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>