<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Moves EMPTY_VALUE_FOUND and XPATH_ERROR scorers to the columns scorers."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.io.html.WebLookupAlgorithm']/properties">
	    <xsl:copy>
			    <xsl:apply-templates mode="a" select="node()|@*">
			    </xsl:apply-templates>
        </xsl:copy>
	</xsl:template>
	
	<!-- A) do not copy (delete) XPATH_ERROR and EMPTY_VALUE_FOUND scoring entries of the parent scorer -->
	<xsl:template mode="a" match="scoringEntry[@key='WLA_XPATH_ERROR' or @key='WLA_EMPTY_VALUE_FOUND']"/>
	
	<xsl:template mode="a" match="columns/column">
		<xsl:copy>
			<!-- check already existing scorer -->
			<xsl:variable name="scorerValue" select="scorer"/>
			<!-- copy existing content -->
			<xsl:apply-templates select="node()|@*"/>
			<xsl:choose>
				<xsl:when test="not($scorerValue)">
					<!-- scorer not defined, create it from parent -->
					<xsl:variable name="vExplainColumn" select="ancestor::node()[local-name()='properties']/scorer/@explanationColumn"/>
					<xsl:variable name="vScoreValue" select="ancestor::node()[local-name()='properties']/scorer/@scoreColumn"/>
					
					<xsl:element name="scorer">
						<xsl:choose>
							<xsl:when test="$vExplainColumn">
								<xsl:attribute name="explanationColumn"><xsl:value-of select="$vExplainColumn"/></xsl:attribute>
							</xsl:when>
						</xsl:choose>
					   <xsl:choose>
					   		<xsl:when test="$vScoreValue">
					   			<xsl:attribute name="scoreColumn"><xsl:value-of select="$vScoreValue"/></xsl:attribute>
					   		</xsl:when>
					   </xsl:choose>
					   <xsl:element name="scoringEntries">
					   		<xsl:copy-of select="ancestor::node()[local-name()='properties']/scorer/scoringEntries/scoringEntry[@key='WLA_XPATH_ERROR' or @key='WLA_EMPTY_VALUE_FOUND']">
					   </xsl:copy-of>
					   </xsl:element>
					</xsl:element>
				</xsl:when>
			</xsl:choose>			
		</xsl:copy>
	</xsl:template>
	
	<xsl:template mode="a" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="a" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
