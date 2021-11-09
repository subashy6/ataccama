<?xml version="1.0" encoding="UTF-8" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
				xmlns:ver="http://www.ataccama.com/purity/version"
				ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
				ver:name="Creates global 'errorHandlingStrategy' and 'dataFormatParameters' if not present">
	
	<!--
		Pokud nejsou u TextFileReaderu definovany errorHandlingStrategy
		a globalni dataFormatParameters, vlozi tyto elementy s defaultnim 
		nastavenim (jen putToReject u vsech errorInstruction je nastaveno na 
		false).
		
		Pouzij spolecne s transformaci 10-defaultsToColumnsOfTextFileReader 
		pro uplnou konverzi	na TextFileReader s out_reject endpointem.
	-->
	
	<xsl:template name="defaults" match="step[contains(@className, 'TextFileReader')]/properties">

		<xsl:variable name="dataFormats" select="dataFormatParameters" />
		<xsl:variable name="errorHandling" select="errorHandlingStrategy" />
			
		<xsl:copy>
			<xsl:if test="not($dataFormats)">
				<xsl:element name="dataFormatParameters" >
					<xsl:attribute name="trueValue">true</xsl:attribute>
					<xsl:attribute name="falseValue">false</xsl:attribute>
					<xsl:attribute name="dateFormatLocale">en_US</xsl:attribute>
					<xsl:attribute name="dateTimeFormat">yyyy-MM-dd HH:mm:ss</xsl:attribute>
					<xsl:attribute name="decimalSeparator">.</xsl:attribute>
					<xsl:attribute name="dayFormat">yyyy-MM-dd</xsl:attribute>
				</xsl:element>
			</xsl:if>
	
			<xsl:if test="not($errorHandling)">
				<xsl:element name="errorHandlingStrategy" >
					<xsl:element name="errorInstructions" >
						<xsl:element name="errorInstruction" >
							<xsl:attribute name="errorType">PROCESSING_ERROR</xsl:attribute>
							<xsl:attribute name="dataStrategy">STOP</xsl:attribute>
							<xsl:attribute name="putToLog">true</xsl:attribute>
							<xsl:attribute name="putToReject">false</xsl:attribute>
						</xsl:element>
						<xsl:element name="errorInstruction" >
							<xsl:attribute name="errorType">INVALID_DATE</xsl:attribute>
							<xsl:attribute name="dataStrategy">READ_POSSIBLE</xsl:attribute>
							<xsl:attribute name="putToLog">true</xsl:attribute>
							<xsl:attribute name="putToReject">false</xsl:attribute>
						</xsl:element>
						<xsl:element name="errorInstruction" >
							<xsl:attribute name="errorType">SHORT_LINE</xsl:attribute>
							<xsl:attribute name="dataStrategy">READ_POSSIBLE</xsl:attribute>
							<xsl:attribute name="putToLog">true</xsl:attribute>
							<xsl:attribute name="putToReject">false</xsl:attribute>
						</xsl:element>
						<xsl:element name="errorInstruction" >
							<xsl:attribute name="errorType">UNPARSABLE_FIELD</xsl:attribute>
							<xsl:attribute name="dataStrategy">NULL_VALUE</xsl:attribute>
							<xsl:attribute name="putToLog">true</xsl:attribute>
							<xsl:attribute name="putToReject">false</xsl:attribute>
						</xsl:element>
					</xsl:element>
				</xsl:element>
			</xsl:if>
			
			<xsl:apply-templates/>
			
		</xsl:copy>
	</xsl:template>

	<xsl:template match="node()">
		<xsl:copy>
			<xsl:for-each select="@*">
				<xsl:copy /> 
			</xsl:for-each>
			<xsl:apply-templates/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
