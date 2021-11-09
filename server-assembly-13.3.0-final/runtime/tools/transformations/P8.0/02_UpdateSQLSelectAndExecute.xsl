<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="7.0.0" ver:versionTo="8.0.0"
	ver:name="Removes writeToErrEndPoint from the ErrorHandler">
	
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
	<!-- removes writeToErrEndPoint, when errorHandler is defined it is automatically considered 'true'
	     (like in the JdbcWriter) -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.jdbc.execute.SQLExecute']/properties/errorHandler/writeToErrEndPoint"/> 
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.jdbc.execute.SQLExecute']/properties/errorHandler/@writeToErrEndPoint"/>
	<!-- same thing in the SQLSelect -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.jdbc.execute.SQLSelect']/properties/errorHandler/writeToErrEndPoint"/> 
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.jdbc.execute.SQLSelect']/properties/errorHandler/@writeToErrEndPoint"/>
	
	<!-- removes autoCommit property : autocommit is false by default (like in the JdbcWriter) -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.jdbc.execute.SQLExecute']/properties/autocommit"/> 
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.jdbc.execute.SQLExecute']/properties/@autocommit"/>	
</xsl:stylesheet>