#!/bin/bash

# starts standalone derby database server

(
cd ..

export DQC_HOME=.
export JRE_HOME="$DQC_HOME/../jre"

export JAVA_OPTS=-Dderby.system.home="$DQC_HOME/../derby"

"$DQC_HOME/bin/run_java.sh" org.apache.derby.iapi.tools.run server -noSecurityManager start


)
