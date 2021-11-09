<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Transforms rating for Dictionary Lookup Identifier">

	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']">
		<xsl:copy>
			<xsl:apply-templates select="@*"/>
			<xsl:variable name="classificationAttr" select="properties/@classification" />
			<xsl:variable name="classificationElem" select="properties/classification" />
			<xsl:choose>
				<!-- classification as attribute -->
				<xsl:when test="$classificationAttr != ''">
					<xsl:apply-templates mode="rating">
						<xsl:with-param name="paramClassification" select="$classificationAttr" />
					</xsl:apply-templates>
				</xsl:when>
				<!-- classification as element -->
				<xsl:when test="not($classificationElem)">
					<xsl:apply-templates mode="rating">
						<xsl:with-param name="paramClassification" select="$classificationElem" />
					</xsl:apply-templates>
				</xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="node()|@*" mode="rating" />
				</xsl:otherwise>
			</xsl:choose>
		</xsl:copy>
	</xsl:template>
	
	<!-- remove classification attribute/element -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/@classification" mode="rating" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/classification" mode="rating" />
	
	<!-- remove outputAnyBest from rating -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/rating/rating/@outputAnyBest" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/rating/rating/outputAnyBest" />
	
	<!-- when in "rating" mode, pass classification as parameter -->
	<xsl:template match="node()|@*" mode="rating">
		<xsl:param name="paramClassification" />
		
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="rating">
				<xsl:with-param name="paramClassification" select="$paramClassification" />
			</xsl:apply-templates>
		</xsl:copy>
	</xsl:template>
	
	<!-- transform rating into the rich form -->
	<xsl:template match="properties/rating" mode="rating">
		<xsl:param name="paramClassification" />
		
		<xsl:element name="ratings">
			<xsl:element name="ratingCase">
				<xsl:attribute name="classificationColumn">
					<xsl:value-of select="$paramClassification" />
				</xsl:attribute>
				<xsl:element name="ratings">
					<!-- switch to mormal mode - without parameter -->
					<xsl:apply-templates select="node()|@*" />
				</xsl:element>
			</xsl:element>
		</xsl:element>
	</xsl:template>
	
<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>