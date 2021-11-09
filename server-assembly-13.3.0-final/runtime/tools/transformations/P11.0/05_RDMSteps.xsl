<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.0.0" ver:versionTo="11.0.0"
	ver:name="Change RDM Steps">

	<xsl:template match="step[contains(@className,'com.ataccama.rdm.manager.steps.Rdm')]">
		<step id="{@id}" className="{@className}">
			<properties>			
				<xsl:for-each select="properties/@*">
					<xsl:if test="name()!='username' and name()!='password' and name()!='url'">
						<xsl:attribute name="{name()}"><xsl:value-of select="."/></xsl:attribute>
					</xsl:if>							
				</xsl:for-each>
				<xsl:attribute name="url" select="'rdmapp'"/>
				<credentials password="{properties/@password}" username="{properties/@username}"/>
				<xsl:copy-of select="properties/columns"/>
				<xsl:copy-of select="properties/data"/>
			</properties>
			<xsl:copy-of select="visual-constraints"/>
		</step>
	</xsl:template>

	<xsl:template match="connection[target/@step=//step[@className='com.ataccama.rdm.manager.steps.RdmSynchronizeStep']/@id]">
		<connection className="com.ataccama.dqc.model.elements.connections.StandardFlowConnection" disabled="false">
	        <source step="{source/@step}" endpoint="out"/>
	        <target step="{target/@step}" endpoint="parameters"/>
	        <visual-constraints>
	            <bendpoints/>
	        </visual-constraints>
	    </connection>		
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*" />
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
