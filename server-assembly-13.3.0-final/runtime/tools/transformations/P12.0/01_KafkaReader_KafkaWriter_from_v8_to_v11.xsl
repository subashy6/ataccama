<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
    xmlns:ver="http://www.ataccama.com/purity/version"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="11.0.0" ver:versionTo="12.0.0"
	ver:name="Remove old not needed kafkaProperty list from properties of KafkaReader and KafkaWriter (change from Kafka v8 to v11)">
    <xsl:template match="step[@className='com.ataccama.dqc.streaming.io.reader.KafkaReader']">
        <xsl:element name="step">
            <xsl:attribute name="mode" select="@mode"/>
            <xsl:attribute name="className" select="@className"/>
            <xsl:attribute name="disabled" select="@disabled"/>
            <xsl:attribute name="id" select="@id"/>
            <xsl:element name="properties">
				<xsl:attribute name="server" select="properties/@cluster"/>
				<xsl:attribute name="groupId" select="properties/@groupId"/>
				<xsl:attribute name="topics" select="properties/@topic"/>
				<xsl:attribute name="encoding" select="properties/@encoding"/>
				<xsl:attribute name="readFromBeginning" select="'false'"/>
				<xsl:attribute name="pollOnce" select="'false'"/>
                <xsl:copy-of select="properties/inputFormat"/>
                <xsl:element name="properties"></xsl:element>
                <xsl:copy-of select="properties/shadowColumns"/>
            </xsl:element>
            <xsl:copy-of select="visual-constraints"/>
        </xsl:element>
    </xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.streaming.io.writer.KafkaWriter']">
        <xsl:element name="step">
            <xsl:attribute name="mode" select="@mode"/>
            <xsl:attribute name="className" select="@className"/>
            <xsl:attribute name="disabled" select="@disabled"/>
            <xsl:attribute name="id" select="@id"/>
            <xsl:element name="properties">
				<xsl:attribute name="server" select="properties/@cluster"/>
				<xsl:attribute name="partitionKey" select="properties/@partitionKey"/>
				<xsl:attribute name="topic" select="properties/@topic"/>
				<xsl:attribute name="encoding" select="properties/@encoding"/>
                <xsl:copy-of select="properties/outputFormat"/>
                <xsl:element name="properties"></xsl:element>
                <xsl:copy-of select="properties/shadowColumns"/>
            </xsl:element>
            <xsl:copy-of select="visual-constraints"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
