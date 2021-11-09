<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:comm="http://www.ataccama.com/purity/comment"
	ver:versionFrom="5.3.0" ver:versionTo="6.0.0"
	ver:name="Transforms removed ValidateRC steps to the RCValidator steps.">


	<!-- scoring entries -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.v1.clean.ValidateRCAlgorithm']/properties/scorer/scoringEntries">
		<xsl:variable name="e_expl" select="scoringEntry[@key='RC_TRLR_INVALID']"/>
		<xsl:variable name="e_dummy" select="scoringEntry[@key='RC_DUMMY_DATE']"/>
		<xsl:variable name="e_bn_since" select="RC_DATE_BEFORE_BN_SINCE" />
		<xsl:variable name="e_gener" select="RC_GENERATED"/>
		<xsl:variable name="e_not_gener" select="RC_NOT_GENERATED"/>
		
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
			
			<xsl:choose>
				<xsl:when test="not($e_expl)">
					<xsl:element name="scoringEntry">
						<xsl:attribute name="key">RC_TRLR_INVALID</xsl:attribute>
						<xsl:attribute name="explain">true</xsl:attribute>
					</xsl:element>
				</xsl:when>
			</xsl:choose>
			
			<xsl:choose>
				<xsl:when test="not($e_dummy)">
					<xsl:element name="scoringEntry">
						<xsl:attribute name="key">RC_DUMMY_DATE</xsl:attribute>
						<xsl:attribute name="explain">true</xsl:attribute>
					</xsl:element>
				</xsl:when>
			</xsl:choose>
			
			<xsl:choose>
				<xsl:when test="not($e_bn_since)">
					<xsl:element name="scoringEntry">
						<xsl:attribute name="key">RC_DATE_BEFORE_BN_SINCE</xsl:attribute>
						<xsl:attribute name="explain">true</xsl:attribute>
					</xsl:element>
				</xsl:when>
			</xsl:choose>

			<xsl:choose>
				<xsl:when test="not($e_gener)">
					<xsl:element name="scoringEntry">
						<xsl:attribute name="key">RC_GENERATED</xsl:attribute>
						<xsl:attribute name="explain">true</xsl:attribute>
					</xsl:element>
				</xsl:when>
			</xsl:choose>
			
			<xsl:choose>
				<xsl:when test="not($e_not_gener)">
					<xsl:element name="scoringEntry">
						<xsl:attribute name="key">RC_NOT_GENERATED</xsl:attribute>
						<xsl:attribute name="explain">true</xsl:attribute>
					</xsl:element>
				</xsl:when>
			</xsl:choose>			

		</xsl:copy>
	</xsl:template>

	<!-- processes properties of the ValidateRC step -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.v1.clean.ValidateRCAlgorithm']/properties">		
		
		<xsl:element name="properties">
			<!-- process properties, copy all but 'whenCondition' - for whenCondition prepend some error expression as warning -->
			<xsl:attribute name="whenCondition">
*** THIS STEP WAS AUTOMATICALLY ADAPTED AND REQUIRES MANUAL REVIEW ***
*** ONCE IT IS REVIEWED PLEASE REMOVE THESE LINES ***
				<xsl:choose>
					<xsl:when test="@whenCondition">
						<xsl:value-of select="@whenCondition"/>
					</xsl:when>
				</xsl:choose>
			</xsl:attribute>
			<xsl:for-each select="@*">
				<xsl:choose> 
					<xsl:when test="name() = 'whenCondition'">
						<!-- empty -->
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
			
			<xsl:apply-templates select="node()"/>			
		</xsl:element>
	</xsl:template>
	
	
	<!-- ValidateRC algorithm - replaces ValidateRC with RCValidator -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.v1.clean.ValidateRCAlgorithm']">
		<xsl:message terminate="no">Adapted RCValidator step (id: <xsl:value-of select="@id"></xsl:value-of>) requires manual review</xsl:message>
	   	<xsl:element name="step">
			<xsl:for-each select="@*">
				<xsl:choose>
					<xsl:when test="name() = 'className'">
						<xsl:attribute name="className">cz.adastra.cif.tasks.clean.RCValidatorAlgorithm</xsl:attribute>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
			<xsl:apply-templates select="node()"/>
		</xsl:element>
	</xsl:template>
		
	
	<!-- base copy template -->
	<xsl:template match="node() | @*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>