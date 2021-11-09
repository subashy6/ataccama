<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.9"
	ver:name="Converts 'format' attribute of the Column of TFWriter to appropriate DataFormatParameters">
	
	<!--
		Pro vsechny stepy typu 'TextFileWriter' zkontroluje definice sloupcu 'column', pokud
		je nalezen sloupec obsahujici 'format' parametr je tento parametr zrusen a do 
		pruslusneho 'columnu' je doplnena definice 'DataFormatParameters' s 'dateFormatLocale',
		'dateTimeFormat', 'dayFormat' nactena z tagu. Pokud tag neobsahoval hodnotu 'locale'
		je uvazovana hodnota 'en_US'.	
	-->
	
	
	<!-- column fix -->
	<xsl:template match="node()" mode="fixing">
		<xsl:variable name="name" select="@name" />

		<xsl:variable name="format" select="@format" />
		<xsl:variable name="locale" select="@locale" />

		<xsl:variable name="elName" select="name()"/>

		<xsl:choose>
			<xsl:when test="not($format)">
				<xsl:copy-of select="."/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:element name="{$elName}">
					<xsl:attribute name="name"><xsl:value-of select="$name" /></xsl:attribute>
					<!-- protoze neni jasne jestli se jedna o day nebo datetime napln obe polozky stejnym formatem -->					
					<xsl:element name="dataFormatParameters" >
						<!-- pokud neni locale definovan , predpoklada se en_US -->
						<xsl:choose>
							<xsl:when test="not($locale)">
								<xsl:attribute name="dateFormatLocale">en_US</xsl:attribute>
							</xsl:when> 
							<xsl:otherwise>
								<xsl:attribute name="dateFormatLocale"><xsl:value-of select="$locale"/></xsl:attribute>
							</xsl:otherwise>
						</xsl:choose>						
						<xsl:attribute name="dateTimeFormat"><xsl:value-of select="$format"/></xsl:attribute>
						<xsl:attribute name="dayFormat"><xsl:value-of select="$format"/></xsl:attribute>
					</xsl:element>
					
				</xsl:element>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	
	<!-- column step location -->
	<xsl:template match="step[contains(@className, 'TextFileWriter')]/properties/columns/*">
		<xsl:apply-templates select="." mode="fixing"/>
	</xsl:template>


	<!-- shadow column step location -->
	<xsl:template match="step[contains(@className, 'TextFileWriter')]/properties/shadowColumns/*">
		<xsl:apply-templates select="." mode="fixing"/>
	</xsl:template>
	

	<!-- global copy procesor -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>