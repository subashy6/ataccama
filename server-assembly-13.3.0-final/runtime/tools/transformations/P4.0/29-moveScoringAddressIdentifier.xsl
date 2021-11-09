<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="3.0.0" ver:versionTo="4.0.0"
	ver:name="Replacement: move scoring entries from scorer to attributeScorer (AddressIdentifier)">

	<!--

	-->

	<xsl:template match="step[@className='cz.adastra.cif.tasks.addresses.AddressIdentifier']/properties">

		<xsl:element name="properties">

			<xsl:apply-templates mode="exclude" select="*|@*"/>

			<xsl:if test="scorer">
				<xsl:element name="scorer">
					<xsl:element name="scoringEntries">
						<xsl:for-each select="scorer/scoringEntries/scoringEntry">
							<xsl:variable name="key" select="key|@key" />
							<xsl:choose>
								<xsl:when test="$key='AI_NO_ADDRESS_ID'" />
								<xsl:when test="$key='AI_NO_PATTERN'" />
								<xsl:when test="$key='AI_ID_MISMATCH'" />
								<xsl:when test="$key='AI_SWAP_LRN_SN'" />
								<xsl:when test="$key='AI_UNDECIDED_LRN_SN'" />
								<xsl:otherwise>
									<xsl:copy-of select="."/>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:for-each>
					</xsl:element>
				</xsl:element>
			</xsl:if>

			<xsl:element name="attributeScorer">
				<xsl:element name="scoringEntries">
					<xsl:for-each select="attributeScorer/scoringEntries/scoringEntry">
						<xsl:copy-of select="."/>
					</xsl:for-each>
					<xsl:copy-of select="scorer/scoringEntries/scoringEntry[@key='AI_NO_ADDRESS_ID' or key='AI_NO_ADDRESS_ID']" />
					<xsl:copy-of select="scorer/scoringEntries/scoringEntry[@key='AI_NO_PATTERN' or key='AI_NO_PATTERN']" />
					<xsl:copy-of select="scorer/scoringEntries/scoringEntry[@key='AI_ID_MISMATCH' or key='AI_ID_MISMATCH']" />
					<xsl:copy-of select="scorer/scoringEntries/scoringEntry[@key='AI_SWAP_LRN_SN' or key='AI_SWAP_LRN_SN']" />
					<xsl:copy-of select="scorer/scoringEntries/scoringEntry[@key='AI_UNDECIDED_LRN_SN' or key='AI_UNDECIDED_LRN_SN']" />
				</xsl:element>
			</xsl:element>


		</xsl:element>

	</xsl:template>


	<xsl:template mode="exclude" match="scorer|attributeScorer" />

	<xsl:template mode="exclude" match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates mode="exclude" select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

	<!-- The default copy template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>