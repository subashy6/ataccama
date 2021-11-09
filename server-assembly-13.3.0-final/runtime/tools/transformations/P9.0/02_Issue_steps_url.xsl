<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="7.0.0" ver:versionTo="9.0.0"
	ver:name="Converts applicationUrl, user and password to a single server value for IssueImporter and IssueReader steps."
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='com.ataccama.epp.dqc.steps.IssueImporter']/properties | step[@className='com.ataccama.epp.dqc.steps.IssueReader']/properties">
        <xsl:variable name='applicationUrl' select='@applicationUrl|applicationUrl'/>
        <xsl:variable name='user' select='@user|user'/>
        <xsl:variable name='password' select='@password|password'/>
        
		<xsl:copy>
            <xsl:attribute name="server"><xsl:value-of select="concat($user, ':', $password, '@', $applicationUrl)"/></xsl:attribute>
			<xsl:apply-templates select="node()|@*" mode="issueTrackerStep" />
		</xsl:copy>
	</xsl:template>

	<xsl:template match="properties/@applicationUrl | properties/applicationUrl | properties/@user | properties/user | properties/@password | properties/password" mode="issueTrackerStep">
        <!-- empty -->
    </xsl:template>
	
	<xsl:template match="node()|@*" mode="issueTrackerStep">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" mode="issueTrackerStep"/>
		</xsl:copy>
	</xsl:template>	

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
