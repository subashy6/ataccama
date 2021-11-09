<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xsl:stylesheet [
<!ENTITY LF "<xsl:text>&#xA;</xsl:text>">
<!ENTITY TAB "<xsl:text>&#x9;</xsl:text>">
<!ENTITY TB2 "<xsl:text>&#x9;&#x9;</xsl:text>">
<!ENTITY TB3 "<xsl:text>&#x9;&#x9;&#x9;</xsl:text>">
<!ENTITY TB4 "<xsl:text>&#x9;&#x9;&#x9;&#x9;</xsl:text>">
<!ENTITY TB5 "<xsl:text>&#x9;&#x9;&#x9;&#x9;&#x9;</xsl:text>">
]>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.5.0"
	ver:name="RegexMatchingAlgorithm supports more regex pattern definitions">
	
	<xsl:template name="defaults" match="step[contains(@className, 'RegexMatchingAlgorithm')]">
		<xsl:variable name="stepId" select="@id"/>
		<xsl:element name="step">
			<xsl:copy-of select="@*"/>&LF;
			&TAB;&TAB;
			<xsl:element name="properties">&LF;
				&TB3;
				<xsl:element name="expression"><xsl:value-of select="binding/@column"/></xsl:element>&LF;
				&TB3;
				<xsl:element name="regexNameColumn"><xsl:text/></xsl:element>&LF;&LF;
				
				<xsl:for-each select="properties">
				    <xsl:variable name="regexpr" select="@regExpression"/>
					<xsl:call-template name="regex">
						<xsl:with-param name="regexpr" select="$regexpr"/>
						<xsl:with-param name="stepId" select="$stepId"/>
					</xsl:call-template>
					&LF;
					<xsl:call-template name="noMatch"/>
				</xsl:for-each>
				
				&LF;&TB3;
				<xsl:copy-of select="properties/scorer"/>
				&LF;&TB2;
			</xsl:element>&LF;
		&TAB;
		</xsl:element>&LF;
	</xsl:template>
	
	<xsl:template name="regex">
		<xsl:param name="stepId" select="stepId"/>
		<xsl:param name="regexpr" select="regexpr"/>
		&TB3;
		<xsl:element name="regExpressions">&LF;
			&TB4;
			<xsl:element name="regExpression">&LF;
				&TB5;
				<xsl:element name="name"><xsl:value-of select="$stepId"/>#1</xsl:element>
				<xsl:element name="pattern"><xsl:value-of select="$regexpr"/></xsl:element>
				
				<xsl:apply-templates select="node()[name()!='scorer']"/>
				&LF;
			&TB4;
			</xsl:element>&LF;
		&TB3;
		</xsl:element>&LF;
	</xsl:template>
	
	<xsl:template name="noMatch">
		&TB3;
		<xsl:element name="noMatchColumns">&LF;
			<xsl:for-each select="resultColumns/column">
				&TB4;
				<xsl:element name="column">
					<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
					<xsl:if test="@nonMatchValue">
						<xsl:attribute name="value"><xsl:value-of select="@nonMatchValue"/></xsl:attribute>
					</xsl:if>
				</xsl:element>&LF;
			</xsl:for-each>
		&TB3;
		</xsl:element>&LF;
	</xsl:template>
	
	<xsl:template match="step[contains(@className, 'RegexMatchingAlgorithm')]/properties/regExpression">
		<xsl:element name="pattern"><xsl:value-of select="."/></xsl:element>
	</xsl:template>
	
	<xsl:template match="step[contains(@className, 'RegexMatchingAlgorithm')]//resultColumns/column">
		<xsl:element name="column">
			<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
			<xsl:attribute name="substitution"><xsl:value-of select="@replacement"/></xsl:attribute>
		</xsl:element>
	</xsl:template>
	
	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>