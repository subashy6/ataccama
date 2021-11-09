<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
				xmlns:ver="http://www.ataccama.com/purity/version"
				xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
				ver:versionFrom="12.0.0" ver:versionTo="12.6.0"
				ver:name="Changes package of Spark RDD Repartition step">
	<xsl:template match="step/@className[.='com.ataccama.dqc.tasks.flow.SparkRDDRepartition']">
		<xsl:attribute name="className">com.ataccama.dqc.spark.steps.SparkRDDRepartition</xsl:attribute>
	</xsl:template>

	<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
