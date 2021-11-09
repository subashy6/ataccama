<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
				xmlns:ver="http://www.ataccama.com/purity/version"
				xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
				ver:versionFrom="11.0.0" ver:versionTo="12.0.0"
				ver:name="configuration of Kafka online service"
				exclude-result-prefixes="ver">
	<xsl:template match="method[@class='com.ataccama.dqc.streaming.online.service.GenericKafkaMethod']">
		<xsl:element name="method">
			<xsl:attribute name="consumerGroupId" select="@consumerGroupId"/>
			<xsl:attribute name="server" select="@cluster"/>
			<xsl:attribute name="batchSize" select="@batchSize"/>
			<xsl:attribute name="targetTopic" select="@targetTopic"/>
			<xsl:attribute name="class" select="@class"/>
			<xsl:attribute name="sourceTopics" select="@sourceTopic"/>
			<xsl:attribute name="batchTimeout" select="@batchTimeout"/>
			<xsl:element name="consumerProperties"></xsl:element>
			<xsl:copy-of select="inputFormat"/>
			<xsl:copy-of select="outputFormat"/>
			<xsl:element name="producerProperties"></xsl:element>
		</xsl:element>
	</xsl:template>
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>

