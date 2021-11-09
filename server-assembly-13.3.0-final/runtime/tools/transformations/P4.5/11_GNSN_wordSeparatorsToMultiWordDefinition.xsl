<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.14" ver:versionTo="4.5.15"
	ver:name="GuessNameSurname: replace 'wordSeparators' with 'multiWordDefinition' etc.">

	<!--
	
		Replaces 'wordSeparators' tag with newly introduced 'multiWordDefinition' tag, whose value
		is as follows:
			{MULTIWORD:wordSeparators="X"}
		where X is value of the original tag 'wordSeparators'.
		If 'multiWordDefinition' tag exists already, it's value will remain untouched.	
	
		Furthermore the transformation checks whether the other newly added tags 'wordDefinition' and 
		'interlacedWordDefinition' are present. If so, their values will remain untouched - otherwise 
		these tags are created with their default values:
		
			<wordDefinition>{WORD}</wordDefinition>
			<interlacedWordDefinition>{INTERLACED_WORD}</interlacedWordDefinition>

	-->

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties">
		<xsl:copy>
			<xsl:variable name='wordSeps' select='@wordSeparators|wordSeparators'/>
			
			<xsl:variable name='wrdDef'  select='@wordDefinition|wordDefinition'/>
			<xsl:variable name='iWrdDef' select='@interlacedWordDefinition|interlacedWordDefinition'/>
			<xsl:variable name='mWrdDef' select='@multiWordDefinition|multiWordDefinition'/>
			
			<xsl:choose>
				<xsl:when test="not ($mWrdDef)">
					<!-- wordDefinition not defined yet -->
					<xsl:choose>
						<xsl:when test="not ($wordSeps)">
							<!-- old style tag not found, create default value -->
							<xsl:attribute name='multiWordDefinition'>{MULTIWORD:wordSeparators="-'`""~"}</xsl:attribute>
						</xsl:when>
						<xsl:otherwise>
							<xsl:attribute name='multiWordDefinition'>{MULTIWORD:wordSeparators="<xsl:value-of select="$wordSeps"/>"}</xsl:attribute>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:when>
			</xsl:choose>
			
			<xsl:choose>	
				<xsl:when test="not ($wrdDef)">
					<xsl:attribute name="wordDefinition">{WORD}</xsl:attribute>
				</xsl:when>
			</xsl:choose>
			
			<xsl:choose>
				<xsl:when test="not ($iWrdDef)">
					<xsl:attribute name="interlacedWordDefinition">{INTERLACED_WORD}</xsl:attribute>
				</xsl:when>
			</xsl:choose>
			
			<xsl:apply-templates select="@*|node()" />
		</xsl:copy>
	</xsl:template>

	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/wordSeparators" />
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.GuessNameSurnameAlgorithm']/properties/@wordSeparators" />

	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>