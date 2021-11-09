<?xml version="1.0" encoding="UTF-8" ?>

<xsl:stylesheet 
		xmlns:ver="http://www.ataccama.com/purity/version" version="1.0"
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
		ver:name="Replacement: 'locale' and 'format' to 'dataFormatParameters' (TextFileReader)">
	
	<!--
	
		Pokud je definovan format pro vstupni sloupec, je pro dany sloupec vygenerovan
		subelement dataFormatParameters. Podle obsahu parametru 'type', pak DFP obsahuje:
		
		- 	pro typ boolean, rozparsovane hodnoty odpovidajici true/false z retezce parameteru 'format'
		-	pro ostatni ('day' a 'datetime') se do DFP zapisuje hodnota 'dayFormat' a 'dateTimeFormat'
			(obe jsou nastaveny na hodnotu nactenou z parametru 'format') a hodnota 'locale'. Ta 
			obsahuje hodnotu nactenou ze vstupniho parametru 'locale' nebo defaultni hodnotu 
			('en_US') pokud na vstupu 'locale' nebylo definovano.
			 
	-->

	<xsl:template name="getTrueValue">
		<xsl:param name="list" select="string(.)" />
		<xsl:value-of select="substring-before($list, '|')"/>
	</xsl:template>

	<xsl:template name="getFalseValue">
		<xsl:param name="list" select="string(.)" />
		<xsl:value-of select="substring-after($list, '|')"/>	
	</xsl:template>


	<!-- adds DFP for boolean datatype --> 
	<xsl:template name="processBoolean">
		<xsl:param name="strFormat" select="string(.)"/>
	  	<!--  read true value -->
		<xsl:variable name="trueValue">
			<xsl:call-template name="getTrueValue">
				<xsl:with-param name="list" select="$strFormat"/>
			</xsl:call-template>
		</xsl:variable>
		
		<!-- read false value -->

		<xsl:variable name="falseValue">
			<xsl:call-template name="getFalseValue">
				<xsl:with-param name="list" select="$strFormat"/>
			</xsl:call-template>
		</xsl:variable>	
		
		<xsl:element name="dataFormatParameters">
			<xsl:attribute name="trueValue"><xsl:value-of select="$trueValue"/></xsl:attribute>
			<xsl:attribute name="falseValue"><xsl:value-of select="$falseValue"/></xsl:attribute>
		</xsl:element>
	</xsl:template>


	<!-- adds DFP for day/datetime types -->
	<xsl:template name="processDaytype">
		<xsl:param name="dLocale" select="string(.)"/>
		<xsl:param name="dFormat" select="string(.)"/>
		<!-- because it's not clear which datatype is used, fill DFPparameters for them both (DAY,DATETIME) -->					
		<xsl:element name="dataFormatParameters" >
			<!-- if not defined, en_US is assumed -->
			<xsl:choose>
				<xsl:when test="not($dLocale)">
					<xsl:attribute name="dateFormatLocale">en_US</xsl:attribute>
				</xsl:when> 
				<xsl:otherwise>
					<xsl:attribute name="dateFormatLocale"><xsl:value-of select="$dLocale"/></xsl:attribute>
				</xsl:otherwise>
			</xsl:choose>						
			<xsl:attribute name="dateTimeFormat"><xsl:value-of select="$dFormat"/></xsl:attribute>
			<xsl:attribute name="dayFormat"><xsl:value-of select="$dFormat"/></xsl:attribute>
		</xsl:element>	
	</xsl:template>


	<xsl:template match="node()" mode="fixing">
		<xsl:variable name="name" select="@name|name" />
		<xsl:variable name="format" select="@format|format" />
		<xsl:variable name="locale" select="@locale|locale" />
		<xsl:variable name="type" select="@type|type"/>		
		<xsl:variable name="elName" select="name()"/>	
	
		<xsl:choose>
			<xsl:when test="not($format)">
				<xsl:copy-of select="."/>
			</xsl:when>
			<xsl:otherwise>
			
				<xsl:element name="{$elName}">
					<xsl:attribute name="name"><xsl:value-of select="$name" /></xsl:attribute>
					<xsl:attribute name="type"><xsl:value-of select="$type" /></xsl:attribute>
					
						<!-- do the DFP insertion only for columns -
		 				 	 shadowColumns must not have DFP -->
		 				<xsl:choose>
							<xsl:when test="ancestor::columns">
							
								<xsl:choose>
									<!-- processing as boolean data type -->						
									<xsl:when test="$type='boolean'">
										<xsl:call-template name="processBoolean">
											<xsl:with-param name="strFormat" select="$format"/>
										</xsl:call-template>		
									</xsl:when>
									<!-- processing as day/datetime data type -->
									<xsl:otherwise>
										<xsl:call-template name="processDaytype">
											<xsl:with-param name="dLocale" select="$locale"/>
											<xsl:with-param name="dFormat" select="$format"/>
										</xsl:call-template>						
									</xsl:otherwise>
								</xsl:choose>
								
							</xsl:when>
						</xsl:choose>
				</xsl:element>

			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	<xsl:template match="step[contains(@className, 'TextFileReader')]/properties/columns/*"> 
		<xsl:apply-templates select="." mode="fixing"/>
	</xsl:template>

	<xsl:template match="step[contains(@className, 'TextFileReader')]/properties/shadowColumns/*">
		<xsl:apply-templates select="." mode="fixing"/>
	</xsl:template>
	
	 
	<!-- global copy procesor -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>