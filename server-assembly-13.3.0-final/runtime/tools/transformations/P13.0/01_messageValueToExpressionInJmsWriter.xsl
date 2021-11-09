<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:fn="http://www.w3.org/2005/xpath-functions"
	ver:versionFrom="12.0.0" ver:versionTo="13.0.0"
	ver:name="Change message value to expression in JmsWriter">

	<xsl:template match="step[@className='com.ataccama.dqc.jms.writer.JmsWriter']/properties/messageProperties">
	    <xsl:copy>
	    	<xsl:for-each select="node()">
	    		<xsl:copy>
					<xsl:attribute name="key">
						<xsl:value-of select="@key"/>
					</xsl:attribute>
					<xsl:if test="@value">
						<xsl:attribute name="value">
							<xsl:text>&quot;</xsl:text>
							<xsl:value-of select="fn:replace(@value, '&quot;', '\\&quot;')"/>
							<xsl:text>&quot;</xsl:text>
						</xsl:attribute>
					</xsl:if>
				</xsl:copy>
			</xsl:for-each>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>