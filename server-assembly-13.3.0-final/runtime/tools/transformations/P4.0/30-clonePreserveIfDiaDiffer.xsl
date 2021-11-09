<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: converts preserveIfDiacriticsDiffers='true' into preserveLastNameDia='true' and preserveFirstNameDia='true' (GNSN)">

	<!--
		prevede preserveIfDiacriticsDiffers na preserveLastNameDia a preserveFirstNameDia
	-->

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties">

		<xsl:variable name="plnd" select="preserveLastNameDia|@preserveLastNameDia" />
		<xsl:variable name="pfnd" select="preserveFirstNameDia|@preserveFirstNameDia" />
		<xsl:variable name="pidd" select="preserveIfDiacriticsDiffers|@preserveIfDiacriticsDiffers" />

		<xsl:element name="properties">

			<xsl:choose>
				<xsl:when test="$pidd='true' and not($plnd) and not($pfnd)">
					<xsl:attribute name="preserveLastNameDia">true</xsl:attribute>
					<xsl:attribute name="preserveFirstNameDia">true</xsl:attribute>
				</xsl:when>
				<xsl:otherwise>
					<xsl:copy-of select="preserveLastNameDia|@preserveLastNameDia"/>
					<xsl:copy-of select="preserveFirstNameDia|@preserveFirstNameDia"/>
					<xsl:copy-of select="preserveIfDiacriticsDiffers|@preserveIfDiacriticsDiffers"/>
				</xsl:otherwise>
			</xsl:choose>

			<xsl:apply-templates mode="exclude" select="*|@*"/>

		</xsl:element>

	</xsl:template>


	<xsl:template mode="exclude" match="node()|@*">
		<xsl:choose>
			<xsl:when test="not(starts-with(name(), 'preserve'))">
				<xsl:copy-of select="."/>
			</xsl:when>
		</xsl:choose>
	</xsl:template>

	<!-- The default copy template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>