<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" exclude-result-prefixes="ver"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.0.0" ver:versionTo="4.5.11"
	ver:name="ColumnBinding elimination">

	<!-- 
	
	for all steps mentioned in the mapping, map the bindings to string (expression, column)
	properties. When all columnBinding-based steps are converted to property-based, all 
	steps will be included in the transformation by default (hence we reduce the size of
	the mapping, as most of the step will not have to be there)  
	
	-->

	<!--
	
	The following string defines the mapping.
	The mapping is a sequence of
	
	[<class name>]
		<optional binding element>
		<binding renames>
	[end]
	
	where <class name> is the step class without the package name,
	<optional binding element> is either an empty string or an expression (bindingElement=<elem>)
	and <binding renames> is a sequence (potentially empty ) of (<old binding>=<new binding>)
	
	Examples:
		[SomeStep]
		[end]
		[SomeStep]
			(bindingElement=bindings)
		[end]
		[SomeStep]
			(input_string=inputString)
			(output_string=outputString)
		[end]
	
	-->

	<xsl:variable name="settings">
		[StripTitlesAlgorithm]
		[end]
		[RCValidatorAlgorithm]
		[end]
		[ValidateRCAlgorithm]
		[end]
		[Join]
		[end]
		[Splitter]
		[end]
		[ValidateICAlgorithm]
		[end]
		[ValidateEmailAlgorithm]
		[end]
		[ValidateIdCardAlgorithm]
		[end]
		[ValidateInResAlgorithm]
		[end]
		[ValidateRZAlgorithm]
		[end]
		[ValidateVatIdAlgorithm]
		[end]
		[UpdatePersonTypeByIcoRcAlgorithm]
		[end]
		[RandomFilter]
		[end]
		[TransliterateAlgorithm]
		[end]
		[SelectiveTransliterateAlgorithm]
		[end]
		[UpdateGenderAlgorithm]
		[end]
		[WebServiceMonitor]
		[end]
		[ValueReplacer]
		[end]
		[ValidateSKRZAlgorithm]
		[end]
		[TransformLegalFormsAlgorithm]
		[end]
		[TailTrashingAlgorithm]
		[end]
		[TableMatchingAlgorithm]
		[end]
		[StringLookupAlgorithm]
		[end]
		[SplitOutTrailingNumbers]
		[end]
		[SINValidatorAlgorithm]
		[end]
		[SimpleFilter]
		[end]
		[RepositoryKeyConverter]
		[end]
		[HelloFilter]
		[end]
		[ExperimentalExcludeSpacesAlgorithm]
		[end]
		[EraseSpacesInNamesAlgorithm]
		[end]
		[CreateMatchingValueAlgorithm]
		[end]
		[ApplyReplacementsAlgorithm]
		[end]
		[ConvertPhoneNumbersAlgorithm]
		[end]
		[IntelligentSwapNameSurnameAlgorithm]
		[end]
		[AnonymizerAlgorithm]
		[end]
		[UnifyEngine]
			(bindingElement=attributes)
		[end]
		[ApplyTemplateAlgorithm]
		[end]
		[CreatePostalAddress]
		[end]
		[RemapTool]
		[end]
		[KillUnsupportedCharactersAlgorithm]
		[end]
		[GroupSelectorEngine]
		[end]
		[GetBirthDateFromRCAlgorithm]
		[end]
		[GetPersonTypeAlgorithm]
		[end]
		[SwapNameSurnameAlgorithm]
		[end]
		[ManualOverrideBuilder]
		[end]
		[ManualOverrideBuilder]
		[end]
		[IncrementalManualOverrideBuilder]
		[end]
		[SimpleGroupClassifier]
		[end]
		[RepositoryReader]
		[end]
		[RepositoryWriter]
		[end]		
		[ValidateVinAlgorithm]
		[end]
		[ValidatePhoneNumberAlgorithm]
		[end]
		[RVNValidatorAlgorithm]
		[end]
		[GenerateFakeRCAlgorithm]
		[end]
		[StringLookupBuilder]
		[end]
		[IndexedTableBuilder]
		[end]
		[MatchingLookupBuilder]
		[end]
		[SelectiveMatchingLookupBuilder]
		[end]
		[StatisticsAlgorithm]
		[end]
		[GuessNameSurnameAlgorithm]
		[end]
		[SelectiveResLookupAlgorithm]
		[end]		
		[GenericParserAlgorithm]
		[end]
		[AddressIdentifier]
			(bindingElement=outputComponents)
		[end]
	</xsl:variable>


	<!-- *the* dark magic starts here. You are not expected to understand it O:-) -->

	<xsl:template match="step">
		<xsl:variable name='className'><xsl:call-template name='getLastSegment'>
			<xsl:with-param name='what' select='@className'/>
		</xsl:call-template></xsl:variable>
		<xsl:variable name='classSelector' select='concat("[", $className, "]")'/>
		<xsl:choose>
			<xsl:when test='contains($settings, $classSelector)'>
				<xsl:copy>
					<xsl:apply-templates select="@*"/>
					<xsl:apply-templates select="node()[local-name() != 'binding' and local-name() != 'properties']"/>
					<properties>
						<xsl:apply-templates select="properties/node()|properties/@*"/>
						<xsl:call-template name='processBindings'>
							<xsl:with-param name='bindingInfo' select='substring-before(substring-after($settings, $classSelector), "[end]")'/>
							<xsl:with-param name='bindings' select='binding'/>
						</xsl:call-template>
					</properties>
				</xsl:copy>
			
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
					<xsl:apply-templates select="node()|@*"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template name='processBindings'>
		<xsl:param name='bindingInfo'/>
		<xsl:param name='bindings'/>
		<xsl:choose>
			<xsl:when test='contains($bindingInfo, "(bindingElement=")'>
				<xsl:variable name='elemName' select='translate(substring-before(substring-after($bindingInfo, "(bindingElement="), ")"), " ", "")'/>
				<xsl:variable name='bindRest' select='substring-after(substring-after($bindingInfo, "(bindingElement="), ")")'/>
				<xsl:element name='{$elemName}'>
					<xsl:call-template name='processBindingsWorker'>
						<xsl:with-param name='bindingInfo' select='$bindRest'/>
						<xsl:with-param name='bindings' select='$bindings'/>
					</xsl:call-template>				
				</xsl:element>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name='processBindingsWorker'>
					<xsl:with-param name='bindingInfo' select='$bindingInfo'/>
					<xsl:with-param name='bindings' select='$bindings'/>
				</xsl:call-template>				
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template name='processBindingsWorker'>
		<xsl:param name='bindingInfo'/>
		<xsl:param name='bindings'/>
		<xsl:for-each select='$bindings'>
			<xsl:variable name='name' select='@name'/>
			<xsl:variable name='nameSelector' select='concat("(",$name, "=") '/>
			<xsl:variable name='column' select='@column'/>
			<xsl:choose>
				<xsl:when test='contains($bindingInfo, $nameSelector)'>
					<xsl:call-template name="writeBinding">
						<xsl:with-param name='name' select='translate(substring-before(substring-after($bindingInfo, $nameSelector), ")"), " ", "")'/>
						<xsl:with-param name='value' select='$column'/>
					</xsl:call-template>
				</xsl:when>
				<xsl:otherwise>
					<xsl:call-template name="writeBinding">
						<xsl:with-param name='name' select='$name'/>
						<xsl:with-param name='value' select='$column'/>
					</xsl:call-template>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>
	
	<xsl:template name='writeBinding'>
		<xsl:param name='name'/>
		<xsl:param name='value'/>
		<xsl:choose>
			<xsl:when test='$value = "in" or $value="is" '>
				<xsl:element name='{$name}'>[<xsl:value-of select='$value'/>]</xsl:element>
			</xsl:when>
			<xsl:otherwise>
				<xsl:element name='{$name}'><xsl:value-of select='$value'/></xsl:element>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	
	
	<!-- note that the formatting of the following template must reamin exactly as it is. Otherwise,
	the entire transformation may stop working. -->
	<xsl:template name='getLastSegment'><xsl:param name='what'/><xsl:choose>
		<xsl:when test='contains($what, ".")'><xsl:call-template name='getLastSegment'>
			<xsl:with-param name='what' select='substring-after($what, ".")'/>
		</xsl:call-template></xsl:when>
		<xsl:otherwise><xsl:value-of select='$what'/></xsl:otherwise>
	</xsl:choose></xsl:template>

	<!-- Behold, my child! You are half the way on your path to XSLT Nirvana :-D -->

	<!-- The default copy template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>