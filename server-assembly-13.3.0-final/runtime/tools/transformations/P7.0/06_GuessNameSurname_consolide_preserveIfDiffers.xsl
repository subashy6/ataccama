<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Consolidates preserve if diacritics differs for GuessNameSurname algorithm"
	xmlns:java_functions="http://xml.apache.org/xalan/java">

	<!-- delete the old properties -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/@preserveFirstNameDia" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/@preserveLastNameDia" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/@preserveIfDiacriticsDiffers" />
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/preserveFirstNameDia" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/preserveLastNameDia" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/preserveIfDiacriticsDiffers" />
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.MultiplicativeGuessNameSurnameAlgorithm']/properties/@preserveFirstNameDia" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.MultiplicativeGuessNameSurnameAlgorithm']/properties/@preserveLastNameDia" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.MultiplicativeGuessNameSurnameAlgorithm']/properties/@preserveIfDiacriticsDiffers" />
	
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.MultiplicativeGuessNameSurnameAlgorithm']/properties/preserveFirstNameDia" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.MultiplicativeGuessNameSurnameAlgorithm']/properties/preserveLastNameDia" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.MultiplicativeGuessNameSurnameAlgorithm']/properties/preserveIfDiacriticsDiffers" />

	<!-- analyze old content and consolide -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm' or @className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties">
		<xsl:copy>
			<xsl:variable name="attrFirstName" select="@preserveFirstNameDia" />
			<xsl:variable name="elemFirstName" select="preserveFirstNameDia" />
			<xsl:variable name="F" select="concat($attrFirstName, $elemFirstName)" />
			
			<xsl:variable name="attrLastName" select="@preserveLastNameDia" />
			<xsl:variable name="elemLastName" select="preserveLastNameDia" />
			<xsl:variable name="L" select="concat($attrLastName, $elemLastName)" />
			
			<xsl:variable name="attrBoth" select="@preserveIfDiacriticsDiffers" />
			<xsl:variable name="elemBoth" select="preserveIfDiacriticsDiffers" />
			<xsl:variable name="B" select="concat($attrBoth, $elemBoth)" />

			<xsl:variable name="FL" select="concat(concat($F,'-'),$L)" />
			<xsl:variable name="FLB" select="concat(concat($FL, '-'), $B)" />
			
			<xsl:apply-templates select="@*"/>

			<xsl:choose>
				<!-- BOTH field missing -->
				<xsl:when test="not($B)">
					<xsl:call-template name="processFL">
						<xsl:with-param name="F" select="$F" />
						<xsl:with-param name="L" select="$L" />
					</xsl:call-template>
				</xsl:when>
				
				<!-- BOTH present, any other missing -->
				<xsl:when test="(not($F) or not($L)) and boolean($B)">
					<xsl:call-template name="processFLB">
						<xsl:with-param name="F" select="$F" />
						<xsl:with-param name="L" select="$L" />
						<xsl:with-param name="B" select="$B" />
					</xsl:call-template>
				</xsl:when>
				
				<!-- all fields present -->
				<xsl:otherwise>
					<xsl:call-template name="processAll">
						<xsl:with-param name="FL" select="$FL" />
						<xsl:with-param name="FLB" select="$FLB" />
						<xsl:with-param name="id" select="../@id" />
					</xsl:call-template>
				</xsl:otherwise>
			</xsl:choose>
			
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template name="processAll">
		<xsl:param name="FL" />
		<xsl:param name="FLB" />
		<xsl:param name="id" />
		
		<xsl:choose>
			<xsl:when test="$FL = 'true-true'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_BOTH'" />
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$FLB = 'false-true-false'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_LASTNAME'" />
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$FLB = 'false-true-true'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_LASTNAME'" />
				</xsl:call-template>
				<xsl:message terminate="no">Check your current preserve* related settings for step '<xsl:value-of select="$id" />'.</xsl:message>
			</xsl:when>
			<xsl:when test="$FLB = 'true-false-false'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_FIRSTNAME'" />
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$FLB = 'true-false-true'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_FIRSTNAME'" />
				</xsl:call-template>
				<xsl:message terminate="no">Check your current preserve* related settings for step '<xsl:value-of select="$id" />'.</xsl:message>
			</xsl:when>
			<xsl:when test="$FLB = 'false-false-false'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_NONE'" />
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$FLB = 'false-false-true'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_NONE'" />
				</xsl:call-template>
				<xsl:message terminate="no">Check your current preserve* related settings for step '<xsl:value-of select="$id" />'.</xsl:message>
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	
	<xsl:template name="processFL">
		<xsl:param name="F" />
		<xsl:param name="L" />
		
		<xsl:choose>
			<xsl:when test="$F = 'true' and $L = 'true'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_BOTH'" />
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$F = 'true'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_FIRSTNAME'" />
				</xsl:call-template>
			</xsl:when>
			<xsl:when test="$L = 'true'">
				<xsl:call-template name="createPreserveIfDiffers">
					<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_LASTNAME'" />
				</xsl:call-template>
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	
	<xsl:template name="processFLB">
		<xsl:param name="F" />
		<xsl:param name="L" />
		<xsl:param name="B" />

			<xsl:choose>
				<xsl:when test="$F = 'true' and $B = 'false'">
					<xsl:call-template name="createPreserveIfDiffers">
						<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_FIRSTNAME'" />
					</xsl:call-template>
				</xsl:when>
				<xsl:when test="$L = 'true' and $B = 'false'">
					<xsl:call-template name="createPreserveIfDiffers">
						<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_LASTNAME'" />
					</xsl:call-template>
				</xsl:when>
				<xsl:when test="$F = 'false' and $B = 'true'">
					<xsl:call-template name="createPreserveIfDiffers">
						<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_LASTNAME'" />
					</xsl:call-template>
				</xsl:when>
				<xsl:when test="$L = 'false' and $B = 'true'">
					<xsl:call-template name="createPreserveIfDiffers">
						<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_FIRSTNAME'" />
					</xsl:call-template>
				</xsl:when>
				<xsl:when test="$B = 'true'">
					<xsl:call-template name="createPreserveIfDiffers">
						<xsl:with-param name="paramPreserveFlag" select="'PRESERVE_BOTH'" />
					</xsl:call-template>
				</xsl:when>
			</xsl:choose>
	</xsl:template>
	
	<xsl:template name="createPreserveIfDiffers">
		<xsl:param name="paramPreserveFlag" />
		
		<xsl:attribute name="preserveIfDiffers"><xsl:value-of select="$paramPreserveFlag" /></xsl:attribute>
	</xsl:template>

	<!-- the attribute-aware default template -->

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>