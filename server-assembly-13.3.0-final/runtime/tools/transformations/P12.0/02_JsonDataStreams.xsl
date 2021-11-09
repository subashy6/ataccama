<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="11.0.0" ver:versionTo="12.0.0"
	ver:name="Split json stream configs; add support for record number limitation.">
	<!-- root data stream -->
	<xsl:template match="step[
		@className='com.ataccama.dqc.tasks.io.json.call.JsonCall'
		or @className='com.ataccama.dqc.tasks.io.json.parser.JsonParser'
		or @className='com.ataccama.dqc.tasks.io.json.reader.JsonReader'
		]/properties/reader/dataStreams/jsonStreamConfig">
		<!--  change the name of the element -->
		<xsl:element name="rootJsonStreamConfig">
			<!-- add new attributes -->
			<xsl:attribute name="minOneRecord">false</xsl:attribute>
			<xsl:attribute name="maxOneRecord">false</xsl:attribute>
			<!-- process existing content recursively -->
			<xsl:apply-templates select="@*|node()" />
			<!-- add scorer with explanations -->
			<scorer>
				<scoringEntries>
					<scoringEntry explain="true" score="0" explainAs="WLA_NOT_FOUND" key="WLA_NOT_FOUND"/>
					<scoringEntry explain="true" score="0" explainAs="WLA_MULTIPLE" key="WLA_MULTIPLE"/>
				</scoringEntries>
			</scorer>
		</xsl:element>
	</xsl:template>
	<!-- child data stream -->
	<xsl:template match="step[
		@className='com.ataccama.dqc.tasks.io.json.call.JsonCall'
		or @className='com.ataccama.dqc.tasks.io.json.parser.JsonParser'
		or @className='com.ataccama.dqc.tasks.io.json.reader.JsonReader'
		]/properties/reader/dataStreams/jsonStreamConfig/dataStreams//jsonStreamConfig">
		<!--  change the name of the element -->
		<xsl:element name="childJsonStreamConfig">
			<!-- add new attributes -->
			<xsl:attribute name="minOneRecord">false</xsl:attribute>
			<xsl:attribute name="maxOneRecord">false</xsl:attribute>
			<!-- process existing content recursively -->
			<xsl:apply-templates select="@*|node()" />
			<!-- add scorer with explanations -->
			<scorer>
				<scoringEntries>
					<scoringEntry explain="true" score="0" explainAs="WLA_NOT_FOUND" key="WLA_NOT_FOUND"/>
					<scoringEntry explain="true" score="0" explainAs="WLA_MULTIPLE" key="WLA_MULTIPLE"/>
					<scoringEntry explain="true" score="0" explainAs="WLA_PARENT" key="WLA_PARENT"/>
				</scoringEntries>
			</scorer>
		</xsl:element>
	</xsl:template>
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
