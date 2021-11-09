@echo off

set DQC_HOME=..\..

echo Exporting data from UMC

mkdir data\out
call "%DQC_HOME%\bin\runcif.bat" -runtimeConfig umc.runtimeConfig read_umc.plan

echo Importing data to Keycloak

import_to_keycloak.bat data\out