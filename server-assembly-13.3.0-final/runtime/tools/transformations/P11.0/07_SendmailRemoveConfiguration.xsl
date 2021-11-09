<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.0.0" ver:versionTo="11.0.0"
	ver:name="Remove Sendmail Config from Sendmail">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.experimental.sendmail.SendmailAlgorithm']/properties">
		<xsl:copy>
			<xsl:if test="sendmailConfig">
				<xsl:if test="sendmailConfig/@charset">
					<xsl:attribute name="charset"><xsl:value-of select="sendmailConfig/@charset"/></xsl:attribute>
				</xsl:if>
				<xsl:if test="sendmailConfig/@from">
					<xsl:attribute name="from"><xsl:value-of select="sendmailConfig/@from"/></xsl:attribute>
				</xsl:if>
			</xsl:if>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.experimental.sendmail.SendmailAlgorithm']/properties/sendmailConfig"/>

<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
