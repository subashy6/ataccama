<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="2.0"
	exclude-result-prefixes="xs xdt err fn"
	xmlns:err="http://www.w3.org/2005/xqt-errors"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:fn="http://www.w3.org/2005/xpath-functions" 
	xmlns:xdt="http://www.w3.org/2005/xpath-datatypes"	
	xmlns:xs="http://www.w3.org/2001/XMLSchema"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Rename: DataFormatIntegrator-&gt;Union, VerticalMerge-&gt;Join, Sink-&gt;UnionSame, UniversalConsumer-&gt;Trash">
	<!--
		Zajistuje prejmenovani algoritmu
			DataFormatIntegrator na Union
			VerticalMergeAlgorithm na Join
			Sink na UnionSame
			UniversalConsumer na Trash
		
		Tj. meni prislusne atributy obsahujici kompletni cestu ke tride za cestu k nove tride.
	-->

	<xsl:template match="//@className">
		<xsl:choose>
			<!-- DataFormatIntegrator to Union -->
			<xsl:when test=".=&quot;cz.adastra.cif.tasks.flow.DataFormatIntegrator&quot;">
				<xsl:attribute name="className">cz.adastra.cif.tasks.flow.Union</xsl:attribute>
			</xsl:when>
			
			<!-- VerticalMerge  to  Join -->
			<xsl:when test=".=&quot;cz.adastra.cif.tasks.merge.VerticalMergeAlgorithm&quot;">
				<xsl:attribute name="className">cz.adastra.cif.tasks.merge.Join</xsl:attribute>
			</xsl:when>
			
			<!-- Sink  to  UnionSame -->
			<xsl:when test=".=&quot;cz.adastra.cif.tasks.conditions.Sink&quot;">
				<xsl:attribute name="className">cz.adastra.cif.tasks.conditions.UnionSame</xsl:attribute>
			</xsl:when>
			
			<!-- UniversalConsumer to  Trash -->
			<xsl:when test=".=&quot;cz.adastra.cif.tasks.io.UniversalConsumer&quot;">
				<xsl:attribute name="className">cz.adastra.cif.tasks.io.Trash</xsl:attribute>
			</xsl:when>
									
			<xsl:otherwise>
				<xsl:attribute name="className">
					<xsl:value-of select="."/>
				</xsl:attribute>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>