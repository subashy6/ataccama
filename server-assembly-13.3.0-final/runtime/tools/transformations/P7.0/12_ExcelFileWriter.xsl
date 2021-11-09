<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Converts ExcelFileWriter"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.msoffice.excel.write.ExcelFileWriter']/properties">
		<xsl:element name="properties">
			<xsl:copy-of select="@fileName"/>
			<xsl:if test="@overwriteFile = 'false'">
				<xsl:attribute name="templateFile">original_<xsl:value-of select="@fileName"/></xsl:attribute>
			</xsl:if>
			<xsl:copy-of select="@excel2007"/>
			<xsl:copy-of select="@dateFormat"/>
			<xsl:element name="inputs">
				<xsl:element name="excelSheetInput">
					<xsl:attribute name="inputName">in</xsl:attribute>
					<xsl:copy-of select="@sheet"/>
					<xsl:copy-of select="@sheetName"/>
					<xsl:copy-of select="@clearSheet"/>
					<xsl:copy-of select="@startCell"/>
					<xsl:copy-of select="@writeHeader"/>
					<xsl:copy-of select="@writeAllColumns"/>
					<xsl:copy-of select="columns"/>
				</xsl:element>
			</xsl:element>
		</xsl:element>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
