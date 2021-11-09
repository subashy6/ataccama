<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.18"
	ver:name="Replacement: 'doTrash' to 'fullTrashScope' (parsing algorithms)">

	<!--
	    nahrada doTrash za fullTrashScope - nejprve v elementech a pak v atributech
	    pokud neni doTrash pritomen, nastaveni fulTrashScope na false
	-->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm' or @className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm' or @className='cz.adastra.cif.tasks.clean.ValidatePhoneNumberAlgorithm']/properties">
		<xsl:copy>
			<xsl:variable name='trash' select='@doTrash|doTrash'/>
			<xsl:choose>
				<xsl:when test="not ($trash)">
					<xsl:attribute name='fullTrashScope'>false</xsl:attribute>
				</xsl:when>
				<xsl:otherwise>
					<xsl:attribute name='fullTrashScope'><xsl:value-of select="$trash"/></xsl:attribute>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:apply-templates />
		</xsl:copy>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.parse.GenericParserAlgorithm' or @className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm' or @className='cz.adastra.cif.tasks.clean.ValidatePhoneNumberAlgorithm']/properties/doTrash">
		<!-- vynechat doTrash nody, pokud jsou -->
	</xsl:template>

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>