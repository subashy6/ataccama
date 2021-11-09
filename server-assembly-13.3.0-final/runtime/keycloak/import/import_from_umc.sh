#!/bin/bash

set -e

DQC_HOME=${DQC_HOME:-../..}

echo "Exporting data from UMC"

mkdir -p data/out
"$DQC_HOME/bin/runcif.sh" -runtimeConfig umc.runtimeConfig read_umc.plan

echo "Importing data to Keycloak"

./import_to_keycloak.sh data/out