<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
	xmlns:ver="http://www.ataccama.com/purity/version"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	ver:versionFrom="4.5.12" ver:versionTo="4.5.13"
	ver:name="Change: invalid data definitions are grouped to 'invalidDataDefinitions' tag now">	 
 
 	<!-- 
 		Updates changes in the ValidateBankAccountCZ algorithm:
 		moves tags 'invalidDataDefinitionBankId' and 'invalidDataDefinitionBankAccount'
 		to the newly created tag 'invalidDataDefinitions' that groups them 
 	-->
 
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.bank.account.ValidateBankAccountNumberCZ']/properties/
						*[name() = 'invalidDataDefinitionBankId' or 
						  name() = 'invalidDataDefinitionBankAccount']">
		<!-- skip already processed -->
	</xsl:template>
 
 
	<xsl:template match="step[@className='cz.adastra.cif.tasks.clean.bank.account.ValidateBankAccountNumberCZ']/properties">
		<xsl:element name='properties'>
			<xsl:copy-of select="@*"/>
	
				<xsl:variable name='present' select='invalidDataDefinitions'/>
				<xsl:choose>
					<xsl:when test="not($present)">
							<xsl:element name='invalidDataDefinitions'>
								<xsl:copy-of select="invalidDataDefinitionBankId"/>
								<xsl:copy-of select="invalidDataDefinitionBankAccount"/>
							</xsl:element>
							<!-- <xsl:apply-templates mode="skip"/> -->
							<xsl:apply-templates/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates/>
					</xsl:otherwise>
				</xsl:choose>
				
		</xsl:element>
	</xsl:template>


	<!-- the attribute-aware default template -->
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>