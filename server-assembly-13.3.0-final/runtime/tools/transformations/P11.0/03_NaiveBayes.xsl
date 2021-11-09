<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="10.0.0" ver:versionTo="11.0.0"
	ver:name="Changes in input of Naive Bayes steps">

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.NaiveBayesTrainer']/properties">
		<xsl:copy>
  			<xsl:apply-templates select="node()|@*" />

			<xsl:element name="columns">
				<xsl:element name="trainerColumn">
		 			<xsl:attribute name="class">com.ataccama.dqc.tasks.classification.columns.TrainerColumnDocument</xsl:attribute>
					<xsl:attribute name="name"><xsl:value-of select="././@inputDocument"/></xsl:attribute>
				</xsl:element>
			</xsl:element>
		</xsl:copy>
 	</xsl:template>

	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.NaiveBayesClassifier']/properties">
		<xsl:copy>
  			<xsl:apply-templates select="node()|@*" />

			<xsl:element name="columns">
				<xsl:element name="testerColumn">
		 			<xsl:attribute name="class">com.ataccama.dqc.tasks.classification.columns.TesterColumnDocument</xsl:attribute>
					<xsl:attribute name="name"><xsl:value-of select="././@inputDocument"/></xsl:attribute>
				</xsl:element>
			</xsl:element>
		</xsl:copy>
 	</xsl:template>
 	
 	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.MultiplicativeNaiveBayesClassifier']/properties">
		<xsl:copy>
  			<xsl:apply-templates select="node()|@*" />

			<xsl:element name="columns">
				<xsl:element name="testerColumn">
		 			<xsl:attribute name="class">com.ataccama.dqc.tasks.classification.columns.TesterColumnDocument</xsl:attribute>
					<xsl:attribute name="name"><xsl:value-of select="././@inputDocument"/></xsl:attribute>
				</xsl:element>
			</xsl:element>
		</xsl:copy>
 	</xsl:template>
 	
 	
 	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.NaiveBayesTrainer']/properties/@inputDocument"/>
 	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.NaiveBayesTrainer']/properties/@featuresLookupFile"/>
 	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.NaiveBayesTrainer']/properties/@classificationsLookupFile"/>
	
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.NaiveBayesClassifier']/properties/@inputDocument"/>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.NaiveBayesClassifier']/properties/@featuresLookupFile"/>
 	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.NaiveBayesClassifier']/properties/@classificationsLookupFile"/>
	
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.MultiplicativeNaiveBayesClassifier']/properties/@inputDocument"/>
	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.MultiplicativeNaiveBayesClassifier']/properties/@featuresLookupFile"/>
 	<xsl:template match="step[@className='com.ataccama.dqc.tasks.classification.MultiplicativeNaiveBayesClassifier']/properties/@classificationsLookupFile"/>
	
	
	<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
