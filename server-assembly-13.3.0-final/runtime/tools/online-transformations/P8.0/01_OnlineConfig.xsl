<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="7.0.0" ver:versionTo="8.0.0"
	ver:name="online configuration changes"
	exclude-result-prefixes="ver">
	
	<xsl:template match="*[*/@class='com.ataccama.dqc.online.config.HttpInputMethod']">
		<service>
			<xsl:apply-templates select="name|configFile|requiredRole|minPoolSize|maxPoolSize|parallelismLevel"/>
			<xsl:apply-templates select="@name|@configFile|@requiredRole|@minPoolSize|@maxPoolSize|@parallelismLevel"/>
			<xsl:choose>
				<xsl:when test="input/format/@class='com.ataccama.dqc.online.config.SoapFormat' and outputs/*[1]/format/@class='com.ataccama.dqc.online.config.SoapFormat'">
					<method class="com.ataccama.dqc.online.cfg.SoapOverHttpMethod">
						<xsl:attribute name="location"><xsl:value-of select="input/@location | input/location"/></xsl:attribute>
						<xsl:attribute name="soapAction"><xsl:value-of select="input/format/@soapAction | input/format/soapAction"/></xsl:attribute>
						<!-- xsl:attribute name="soapVersion"><xsl:value-of select="@soapVersion | soapVersion"/></xsl:attribute-->
						<xsl:apply-templates select="@soapVersion | soapVersion"/>
						<xsl:apply-templates select="input | outputs/*[1]"/>
					</method>
				</xsl:when>
				<xsl:otherwise>
					<method class="com.ataccama.dqc.online.cfg.GenericHttpMethod">
						<xsl:apply-templates select="input/@location | input/location"/>
						<xsl:apply-templates select="input | outputs/*[1]"/>
					</method>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:if test="outputs/*[position()>1]">
				<extraAxtions>
					<action>
						<xsl:apply-templates select="outputs/*[position()>1]"/>
					</action>
				</extraAxtions>
			</xsl:if>
		</service>
	</xsl:template>
	
	<xsl:template match="input[format/@class='com.ataccama.dqc.online.config.SoapFormat' or format/@class='com.ataccama.dqc.online.config.XmlFormat']">
		<inputFormat class="com.ataccama.dqc.online.cfg.xml.XmlInputFormat">
			<xsl:if test="format/@namespace | format/namespace">
				<xsl:attribute name="namespace"><xsl:value-of select="format/@namespace | format/namespace"/></xsl:attribute>
			</xsl:if>
			<xsl:apply-templates select="format/rootSection"/>
		</inputFormat>
	</xsl:template>
	<xsl:template match="node()[(local-name()='outputMethod' or (local-name()='output')) and (format/@class='com.ataccama.dqc.online.config.SoapFormat' or format/@class='com.ataccama.dqc.online.config.XmlFormat')]">
		<outputFormat class="com.ataccama.dqc.online.cfg.xml.XmlOutputFormat">
			<xsl:if test="format/@namespace | format/namespace">
				<xsl:attribute name="namespace"><xsl:value-of select="format/@namespace | format/namespace"/></xsl:attribute>
			</xsl:if>
			<xsl:apply-templates select="format/rootSection"/>
		</outputFormat>
	</xsl:template>
	
	<xsl:template match="input[format/@class='com.ataccama.dqc.online.config.CsvInputFormat']">
		<inputFormat class="com.ataccama.dqc.online.cfg.csv.CsvInputFormat">
			<xsl:apply-templates select="format/* | format/@*[local-name() != 'class']"/>
		</inputFormat>
	</xsl:template>
	<xsl:template match="node()[(local-name()='outputMethod' or (local-name()='output')) and format/@class='com.ataccama.dqc.online.config.CsvOutputFormat']">
		<outputFormat class="com.ataccama.dqc.online.cfg.csv.CsvOutputFormat">
			<xsl:apply-templates select="format/* | format/@*[local-name() != 'class']"/>
		</outputFormat>
	</xsl:template>
	
	<xsl:template match="input[format/@class='com.ataccama.dqc.online.config.json.JsonInputFormat']">
		<inputFormat class="com.ataccama.dqc.online.cfg.json.JsonInputFormat">
			<xsl:apply-templates select="format/* | format/@*[local-name() != 'class']"/>
		</inputFormat>
	</xsl:template>
	<xsl:template match="node()[(local-name()='outputMethod' or (local-name()='output')) and format/@class='com.ataccama.dqc.online.config.json.JsonOutputFormat']">
		<outputFormat class="com.ataccama.dqc.online.cfg.json.JsonOutputFormat">
			<xsl:apply-templates select="format/* | format/@*[local-name() != 'class']"/>
		</outputFormat>
	</xsl:template>
	
	<xsl:template match="input[format/@class='com.ataccama.dqc.online.config.params.ParamsInputFormat']">
		<inputFormat class="com.ataccama.dqc.online.cfg.params.ParamsInputFormat">
			<xsl:apply-templates select="format/* | format/@*[local-name() != 'class']"/>
		</inputFormat>
	</xsl:template>
	
	<xsl:template match="input[format/@class='com.ataccama.dqc.online.config.MultipartInputFormat']">
		<inputFormat class="com.ataccama.dqc.online.cfg.multipart.MultipartInputFormat">
			<parts>
				<xsl:apply-templates select="format/partFormats/partFormat"/>
			</parts>
		</inputFormat>
	</xsl:template>
	<xsl:template match="node()[(local-name()='outputMethod' or (local-name()='output')) and format/@class='com.ataccama.dqc.online.config.MultipartOutputFormat']">
		<outputFormat class="com.ataccama.dqc.online.cfg.multipart.MultipartOutputFormat">
			<parts>
				<xsl:apply-templates select="format/partFormats/partFormat"/>
			</parts>
		</outputFormat>
	</xsl:template>
	
	<xsl:template match="partFormat[ancestor::input]">
		<part>
			<xsl:attribute name="contentId"><xsl:value-of select="@contentId | contentId"/></xsl:attribute>
			<xsl:variable name="className">
				<xsl:choose>
					<xsl:when test="@class='com.ataccama.dqc.online.config.CsvInputFormat'">
						<xsl:value-of select="'com.ataccama.dqc.online.cfg.csv.CsvInputFormat'"/>
					</xsl:when>
					<xsl:when test="@class='com.ataccama.dqc.online.config.XmlFormat'">
						<xsl:value-of select="'com.ataccama.dqc.online.cfg.xml.XmlInputFormat'"/>
					</xsl:when>
				</xsl:choose>
			</xsl:variable>
			<format>
				<xsl:attribute name="class"><xsl:value-of select="$className"/></xsl:attribute>
				<xsl:apply-templates select="node()[local-name() != 'class' and local-name() != 'contentId']"/>
			</format>
		</part>
	</xsl:template>
	
	<xsl:template match="partFormat[ancestor::output]">
		<part>
			<xsl:attribute name="contentId"><xsl:value-of select="@contentId | contentId"/></xsl:attribute>
			<xsl:variable name="className">
				<xsl:choose>
					<xsl:when test="@class='com.ataccama.dqc.online.config.CsvOutputFormat'">
						<xsl:value-of select="'com.ataccama.dqc.online.cfg.csv.CsvOutputFormat'"/>
					</xsl:when>
					<xsl:when test="@class='com.ataccama.dqc.online.config.XmlFormat'">
						<xsl:value-of select="'com.ataccama.dqc.online.cfg.xml.XmlOutputFormat'"/>
					</xsl:when>
				</xsl:choose>
			</xsl:variable>
			<format>
				<xsl:attribute name="class"><xsl:value-of select="$className"/></xsl:attribute>
				<xsl:apply-templates select="node()[local-name() != 'class' and local-name() != 'contentId']"/>
			</format>
		</part>
	</xsl:template>
	
	<xsl:template match="foreignColumns[ancestor::input]">
		<references>
			<xsl:for-each select="*">
			<xsl:element name="xmlReferenceColumn">
				<xsl:attribute name="name"><xsl:value-of select="@name"/></xsl:attribute>
				<xsl:attribute name="referencedStepId"><xsl:value-of select="@stepId"/></xsl:attribute>
				<xsl:attribute name="referencedColumn"><xsl:value-of select="@column"/></xsl:attribute>
			</xsl:element>
			</xsl:for-each>
		</references>
	</xsl:template>
	
	<xsl:template match="*[foreignColumns and ancestor::outputs]">
		<xsl:copy>
			<xsl:if test="foreignColumns/*[1]">
				<xsl:attribute name="parentReference"><xsl:value-of select="foreignColumns/*[1]/@name"/></xsl:attribute>
			</xsl:if>
			<xsl:apply-templates select="@* | node()[local-name() != 'foreignColumns']"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="primaryKeyColumn|@primaryKeyColumn">
		<xsl:attribute name="idColumn"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
		
	<xsl:template match="nodeName|@nodeName">
		<xsl:attribute name="xmlName"><xsl:value-of select="."/></xsl:attribute>
	</xsl:template>
	
	<xsl:template match="@strategy[../parent::columns]">
		<xsl:attribute name="strategy"><xsl:choose>
			<xsl:when test=". = 'text_node' or . = 'TEXT_NODE'">TEXT_NODE</xsl:when>
			<xsl:when test=". = 'attribute' or . = 'ATTRIBUTE'">OPTIONAL_ATTR</xsl:when>
			<xsl:when test=". = 'required' or . = 'REQUIRED'">REQUIRED_ELEM</xsl:when>
			<xsl:when test=". = 'optional' or . = 'OPTIONAL'">OPTIONAL_ELEM</xsl:when>
			<xsl:when test=". = 'nillable' or . = 'NILLABLE'">NILLABLE_ELEM</xsl:when>
			<xsl:otherwise><xsl:value-of select="."/></xsl:otherwise>
		</xsl:choose></xsl:attribute>
	</xsl:template>
	
	<xsl:template match="contentId|@contentId">
		<!-- remove the contentId tag/attribute -->
	</xsl:template>
	
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
