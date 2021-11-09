<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: remove endpoint attribute (Join)">

	<!--
		atribut endpoint prevede do atributu expr/expression jako jmeno zdroje v teckove notaci
		pokud je ve vyrazu neco slozitejsiho nez jen nazev pole, zapise do nej text, ktery na to upozorni a prinuti opravit
	-->

	<xsl:template match="step[@className='cz.adastra.cif.tasks.merge.VerticalMergeAlgorithm' or @className='cz.adastra.cif.tasks.merge.Join']/properties/columnDefinitions/*[@endpoint|endpoint]">
		<xsl:variable name="ep" select="@endpoint|endpoint"/>
		<xsl:variable name="exa" select="@expr|@expression"/>
		<xsl:variable name="exe" select="expr|expression"/>
		<xsl:copy>
			<xsl:copy-of select="@name|name|@type|type" />
			<xsl:choose>
				<xsl:when test="$exa">
					<xsl:attribute name="expression">
						<xsl:call-template name="nahrad">
							<xsl:with-param name="ep" select="$ep"/>
							<xsl:with-param name="exp" select="normalize-space($exa)"/>
						</xsl:call-template>
					</xsl:attribute>
				</xsl:when>
				<xsl:when test="$exe">
					<xsl:element name="expression">
						<xsl:call-template name="nahrad">
							<xsl:with-param name="ep" select="$ep"/>
							<xsl:with-param name="exp" select="normalize-space($exe)"/>
						</xsl:call-template>
					</xsl:element>
				</xsl:when>
			</xsl:choose>
		</xsl:copy>
	</xsl:template>

	<xsl:template name="nahrad">
		<xsl:param name="ep"/>
		<xsl:param name="exp"/>
		<xsl:choose>
			<xsl:when test="contains(translate($exp, ' +/(),.', '********'), '*')">
				<xsl:value-of select="concat('Complex expression, please add &quot;',$ep, '.&quot; before every column name: ', $exp)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="concat($ep, '.', $exp)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<!-- The default copy template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>