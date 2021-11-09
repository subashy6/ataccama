<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:comm="http://www.ataccama.com/purity/comment"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	xmlns:string="xalan://java.lang.String"
	ver:name="Transliterate algorithm was upgraded and the old version is translated to the column assigner using transliterate function.">
    <xsl:template match="step[@className='cz.adastra.cif.tasks.clean.TransliterateAlgorithm']">
       <xsl:element name="step">
	       <xsl:attribute name="className">cz.adastra.cif.tasks.expressions.ColumnAssigner</xsl:attribute>
	       <xsl:attribute name="disabled"><xsl:value-of select="@disabled|disabled"/></xsl:attribute>
	       <xsl:attribute name="mode"><xsl:value-of select="@mode|mode"/></xsl:attribute>
	       <xsl:attribute name="id"><xsl:value-of select="@id|id"/></xsl:attribute>
	       <xsl:attribute name="whenCondition"><xsl:value-of select="@whenCondition|whenCondition"/></xsl:attribute>
	       <xsl:element name="properties">
	          <xsl:element name="assignments">
		          <xsl:element name="assignment">
			       <xsl:attribute name="column"><xsl:value-of select="properties/@out|out"/></xsl:attribute>
			       <xsl:variable name="from" select="string:new(properties/@from|from)"/>
			       <xsl:variable name="to" select="string:new(properties/@to|to)"/>
			       <xsl:variable name="apostrof_regex">'</xsl:variable>
			       <xsl:variable name="apostrof_escaped">\\'</xsl:variable>
			       <xsl:variable name="from_slashes_escaped" select="string:replaceAll($from, '\\', '\\\\')"/>
			       <xsl:variable name="to_slashes_escaped" select="string:replaceAll($to, '\\', '\\\\')"/>
			       <xsl:variable name="from_slashes_escaped_string" select="string:new($from_slashes_escaped)"/>
			       <xsl:variable name="to_slashes_escaped_string" select="string:new($to_slashes_escaped)"/>
			       <xsl:attribute name="expression">transliterate(
			             <xsl:value-of select="properties/@in|in"/>,
			             '<xsl:value-of select="string:replaceAll($from_slashes_escaped_string, $apostrof_regex, $apostrof_escaped)"/>',
			             '<xsl:value-of select="string:replaceAll($to_slashes_escaped_string, $apostrof_regex, $apostrof_escaped)"/>')
			       </xsl:attribute>
		          </xsl:element>
	          </xsl:element>
              <xsl:element name="comm:comment">This step was created by adapting transformation from the old transliterate algorithm.
              </xsl:element>
	       </xsl:element>
	       <xsl:copy-of select="visual-constraints"/>
       </xsl:element>
    </xsl:template>
  
<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>