<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.4.0" ver:versionTo="10.5.0"
	ver:name="Changes package of RegexSplitter">

	<xsl:template match="step/@className[.='com.ataccama.dqc.tasks.nlp.RegexSplitter']">
		<xsl:attribute name="className">com.ataccama.dqc.tasks.text.RegexSplitter</xsl:attribute>
	</xsl:template>

<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
