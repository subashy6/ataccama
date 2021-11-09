<?xml version="1.0" encoding="UTF-8" ?> 
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="5.0.0" ver:versionTo="6.0.0"
	ver:name="Conversion old lookups builders to new LookupBuilder">

	<!-- SL -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.StringLookupBuilder']">
		<xsl:copy>
			<xsl:attribute name="className">cz.adastra.cif.tasks.builders.LookupBuilder</xsl:attribute>
			<xsl:apply-templates select="@*[name()!='className']"/>
			<xsl:apply-templates mode="convSL" select="*"/>
			<xsl:apply-templates select="visual-constraints"/>
		</xsl:copy>
	</xsl:template>

	<!-- default index setting and call convert others -->
	<xsl:template mode="convSL" match="properties">
		<xsl:copy>
			<xsl:attribute name="approximativeIndex">true</xsl:attribute>
			<xsl:attribute name="bestDistanceIndex">false</xsl:attribute>
			<xsl:attribute name="duplicities">first</xsl:attribute>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- ML -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.MatchingLookupBuilder']">
		<xsl:copy>
			<xsl:attribute name="className">cz.adastra.cif.tasks.builders.LookupBuilder</xsl:attribute>
			<xsl:apply-templates select="@*[name()!='className']"/>
			<xsl:apply-templates mode="convML" select="*"/>
			<xsl:apply-templates select="visual-constraints"/>
		</xsl:copy>
	</xsl:template>

	<!-- default index setting and call convert others -->
	<xsl:template mode="convML" match="properties">
		<xsl:copy>
			<xsl:attribute name="approximativeIndex">true</xsl:attribute>
			<xsl:attribute name="bestDistanceIndex">true</xsl:attribute>
			<xsl:attribute name="duplicities">first</xsl:attribute>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- SML -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.SelectiveMatchingLookupBuilder']">
		<xsl:copy>
			<xsl:attribute name="className">cz.adastra.cif.tasks.builders.LookupBuilder</xsl:attribute>
			<xsl:apply-templates select="@*[name()!='className']"/>
			<xsl:apply-templates mode="convSML" select="*"/>
		</xsl:copy>
	</xsl:template>

	<!-- default index setting and call convert others -->
	<xsl:template mode="convSML" match="properties">
		<xsl:copy>
			<xsl:attribute name="approximativeIndex">true</xsl:attribute>
			<xsl:attribute name="bestDistanceIndex">true</xsl:attribute>
			<xsl:attribute name="duplicities">first</xsl:attribute>
			<xsl:apply-templates mode="convSML" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- remove strange props, convert oprions -->
	<xsl:template mode="convSML" match="outputColumn|@outputColumn"/>
	<xsl:template mode="convSML" match="realValue|@realValue"/>
	<xsl:template mode="convSML" match="options">
		<xsl:element name="additionalColumns">
			<xsl:apply-templates mode="convCol" select="*"/>
		</xsl:element>
	</xsl:template>

	<!-- copy others -->
	<xsl:template mode="convSML" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- ITL -->
	<xsl:template match="step[@className='cz.adastra.cif.tasks.builders.IndexedTableBuilder']">
		<xsl:copy>
			<xsl:attribute name="className">cz.adastra.cif.tasks.builders.LookupBuilder</xsl:attribute>
			<xsl:apply-templates select="@*[name()!='className']"/>
			<xsl:apply-templates mode="convITL" select="*"/>
		</xsl:copy>
	</xsl:template>

	<!-- default index setting and call convert others -->
	<xsl:template mode="convITL" match="properties">
		<xsl:copy>
			<xsl:attribute name="approximativeIndex">true</xsl:attribute>
			<xsl:attribute name="bestDistanceIndex">false</xsl:attribute>
			<xsl:attribute name="duplicities">accept</xsl:attribute>
			<xsl:apply-templates mode="convITL" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- if omitDuplicities, copy it, else leave accept -->
	<xsl:template mode="convITL" match="omitDuplicities|@omitDuplicities">
		<xsl:if test=".='true'">
			<xsl:attribute name="duplicities">omit</xsl:attribute>
		</xsl:if>
	</xsl:template>

	<!-- call spec convert of columns -->
	<xsl:template mode="convITL" match="columns">
		<xsl:element name="additionalColumns">
			<xsl:apply-templates mode="convCol1" select="*"/>
		</xsl:element>
	</xsl:template>

	<!-- if the first column refers to the same source as key, remove it -->
	<xsl:template mode="convCol1" match="*">
		<xsl:choose>
			<xsl:when test="position()=1">
				<xsl:variable name="key"><xsl:value-of select="../../@key|../../key"/></xsl:variable>
				<xsl:choose>
					<xsl:when test="$key=@src or $key=src or (not(@src) and not(src) and ($key=@name or $key=name))">
						<xsl:message terminate="no">First column defined in IndexedtableBuilder was equal to key and has been removed</xsl:message>	
					</xsl:when>
					<xsl:when test="not(@src) and not(src) and ($key=@name or $key=name)"/>
					<xsl:otherwise>
						<xsl:apply-templates mode="convCol" select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates mode="convCol" select="."/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<!-- copy others -->
	<xsl:template mode="convITL" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- convert columns src -> expression, for both ITL a SML -->
	<xsl:template mode="convCol" match="src|@src">
		<xsl:attribute name="expression"><xsl:value-of select="."/></xsl:attribute>	
	</xsl:template>

	<!-- copy others of columns -->
	<xsl:template mode="convCol" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="convCol" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

<!--  the attribute-aware default template  -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
</xsl:stylesheet>
