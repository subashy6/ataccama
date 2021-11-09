<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Consolidation of package names for runtime">

<!-- DLI -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.identify.dictionary.DictionaryLookupGenerator']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.addresses.dictionary.DictionaryLookupGenerator</xsl:attribute>
	</xsl:template>
	
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.identify.dictionary.DictionaryLookupReader']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.addresses.dictionary.DictionaryLookupReader</xsl:attribute>
	</xsl:template>
	
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.addresses.prototype.DictionaryLookupIdentifier']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.addresses.dictionary.DictionaryLookupIdentifier</xsl:attribute>
	</xsl:template>

<!-- UirAdrGenerator -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.uiradr.UirAdrGenerator']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.addresses.uiradr.UirAdrGenerator</xsl:attribute>
	</xsl:template>

<!-- methods -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/expertSettings/inputSearchMethod/@class">
		<xsl:attribute name="class"><xsl:choose>
			<xsl:when test=". = 'com.ataccama.dqc.tasks.addresses.prototype.model.searching.AhoCorasickMethod'">com.ataccama.dqc.tasks.addresses.dictionary.model.searching.AhoCorasickMethod</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.tasks.addresses.prototype.model.searching.BoundaryAwareMethod'">com.ataccama.dqc.tasks.addresses.dictionary.model.searching.BoundaryAwareMethod</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.tasks.addresses.prototype.model.searching.WordAwareMethod'">com.ataccama.dqc.tasks.addresses.dictionary.model.searching.WordAwareMethod</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.tasks.addresses.prototype.model.searching.ComposedSearchMethod'">com.ataccama.dqc.tasks.addresses.dictionary.model.searching.ComposedSearchMethod</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.tasks.addresses.prototype.model.searching.SingleComponentElementSearchMethod'">com.ataccama.dqc.tasks.addresses.dictionary.model.searching.SingleComponentElementSearchMethod</xsl:when>
			<xsl:otherwise><xsl:value-of select="@class"/></xsl:otherwise>
		</xsl:choose></xsl:attribute>
	</xsl:template>

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.addresses.prototype.DictionaryLookupIdentifier']/properties/expertSettings/evaluatorDefinition/@class">
		<xsl:attribute name="class"><xsl:choose>
			<xsl:when test=". = 'com.ataccama.dqc.tasks.identify.dictionary.evaluation.LongestToShortestEvaluatorDefinition'">com.ataccama.dqc.tasks.addresses.dictionary.evaluation.LongestToShortestEvaluatorDefinition</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.tasks.identify.dictionary.evaluation.CombiningProposalEvaluatorDefinition'">com.ataccama.dqc.tasks.addresses.dictionary.evaluation.CombiningProposalEvaluatorDefinition</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.tasks.identify.dictionary.evaluation.SingleComponentElementEvaluatorDefinition'">com.ataccama.dqc.tasks.addresses.dictionary.evaluation.SingleComponentElementEvaluatorDefinition</xsl:when>
			<xsl:otherwise><xsl:value-of select="@class"/></xsl:otherwise>
		</xsl:choose></xsl:attribute>
	</xsl:template>

<!-- components -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.identify.dictionary.DictionaryLookupGenerator']/properties/referenceData/components/entityComponent/@class">
		<xsl:attribute name="class"><xsl:choose>
			<xsl:when test=". = 'com.ataccama.dqc.addresses.model.components.DictionaryEntityComponent'">com.ataccama.dqc.addresses.commons.model.components.DictionaryEntityComponent</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.addresses.model.components.DictionaryRegularExpressionComponent'">com.ataccama.dqc.addresses.commons.model.components.DictionaryRegularExpressionComponent</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.addresses.model.components.RegexpEntityComponent'">com.ataccama.dqc.addresses.commons.model.components.RegexpEntityComponent</xsl:when>
			<xsl:when test=". = 'com.ataccama.dqc.addresses.model.components.UnionEntityComponent'">com.ataccama.dqc.addresses.commons.model.components.UnionEntityComponent</xsl:when>
			<xsl:otherwise><xsl:value-of select="@class"/></xsl:otherwise>
		</xsl:choose></xsl:attribute>
	</xsl:template>

<!-- AsyncWriter -->
	<xsl:template match="step[@className='com.ataccama.asyncwriter.AsyncWriter']/@className">
		<xsl:attribute name='classname'>com.ataccama.dqc.tasks.experimental.asyncwriter.AsyncWriter</xsl:attribute>
	</xsl:template>
	
<!-- Adapters -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.io.adapter.execute.AdapterExecute']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.iway.adapter.execute.AdapterExecute</xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.io.adapter.read.AdapterReader']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.iway.adapter.read.AdapterReader</xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.io.adapter.select.AdapterSelect']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.iway.adapter.select.AdapterSelect</xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.io.adapter.write.AdapterWriter']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.iway.adapter.write.AdapterWriter</xsl:attribute>
	</xsl:template>

<!-- MSOffice -->
	<xsl:template match="step[@className='com.ataccama.dqc.msoffice.excel.read.ExcelFileReader']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.msoffice.excel.read.ExcelFileReader</xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.msoffice.excel.write.ExcelFileWriter']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.msoffice.excel.write.ExcelFileWriter</xsl:attribute>
	</xsl:template>

<!-- Reporting -->
	<xsl:template match="step[@className='com.ataccama.dqc.reporting.Reporting']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.reporting.Reporting</xsl:attribute>
	</xsl:template>

<!-- Clean v1 steps -->
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.v1.clean.ApplyTemplateAlgorithm']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.clean.v1.ApplyTemplateAlgorithm</xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.v1.clean.GetBirthDateFromRCAlgorithm']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.clean.v1.GetBirthDateFromRCAlgorithm</xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.v1.clean.GetPersonTypeAlgorithm']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.clean.v1.GetPersonTypeAlgorithm</xsl:attribute>
	</xsl:template>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.v1.clean.UpdatePersonTypeByIcoRcAlgorithm']/@className">
		<xsl:attribute name='className'>com.ataccama.dqc.tasks.clean.v1.UpdatePersonTypeByIcoRcAlgorithm</xsl:attribute>
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
