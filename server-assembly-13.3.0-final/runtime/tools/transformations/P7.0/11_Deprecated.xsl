<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="6.0.0" ver:versionTo="7.0.0"
	ver:name="Step renaming to com.ataccama.dqc.tasks.deprecated">
	<!-- the attribute-aware default template -->

	<xsl:template match="step[
		   @className='com.ataccama.dqc.tasks.clean.CreateMatchingValueAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.EraseSpacesInNamesAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.GenerateFakeRCAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.KillUnsupportedCharactersAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.SplitOutTrailingNumbers'
		or @className='com.ataccama.dqc.tasks.clean.StringLookupAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.SwapNameSurnameAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.TableMatchingAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.TailTrashingAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.ValueReplacer'
		or @className='com.ataccama.dqc.tasks.clean.v1.ApplyTemplateAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.v1.GetBirthDateFromRCAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.v1.GetPersonTypeAlgorithm'
		or @className='com.ataccama.dqc.tasks.clean.v1.UpdatePersonTypeByIcoRcAlgorithm'
		or @className='com.ataccama.dqc.tasks.flow.DataFormatChanger'
		or @className='com.ataccama.dqc.tasks.identify.v2.repository.read.RepositoryReader'
		or @className='com.ataccama.dqc.tasks.identify.v3.repository.read.RepositoryReader'
		or @className='com.ataccama.dqc.tasks.identify.v35.repository.read.RepositoryReader'
		or @className='com.ataccama.dqc.tasks.io.lookup.read.IndexedTableReader'
		or @className='com.ataccama.dqc.tasks.io.lookup.read.MatchingLookupReader'
		or @className='com.ataccama.dqc.tasks.io.lookup.read.SelectiveMatchingLookupReader'
		or @className='com.ataccama.dqc.tasks.io.lookup.read.StringLookupReader'
		]">
		<xsl:copy>
			<xsl:attribute name='className'><xsl:choose>
				<xsl:when test='starts-with(@className, "com.ataccama.dqc.tasks.") '>com.ataccama.dqc.tasks.deprecated<xsl:value-of select="substring-after(@className, 'com.ataccama.dqc.tasks')"/></xsl:when>
				<xsl:otherwise><xsl:value-of select="@className"/></xsl:otherwise>
			</xsl:choose></xsl:attribute>
			<xsl:apply-templates select="@*[local-name() != 'className']"/>
			<xsl:apply-templates select="node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>
