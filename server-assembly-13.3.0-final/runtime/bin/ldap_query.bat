@echo off

rem LDAP query utility

call "%~dp0\run_java.bat" com.ataccama.dqc.tools.ldap.LdapQuery %*
