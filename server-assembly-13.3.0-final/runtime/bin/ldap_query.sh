#!/bin/bash

# LDAP query utility

"${0%/*}/run_java.sh" com.ataccama.dqc.tools.ldap.LdapQuery "$@"
