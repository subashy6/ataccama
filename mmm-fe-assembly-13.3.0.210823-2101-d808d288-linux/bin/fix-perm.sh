#!/usr/bin/env bash

chown 0:0 .
chmod a=rX .

chown -R 0 bin/ doc/ legal/ lib/ plugin/
chmod -R a+rx-w bin/
chmod -R a+rX-w lib/
chmod -R a+rX-w plugin/ && chmod a+wt plugin/ # sticky, they are unzipped

chown -R 2001:2001 etc/ license/ log/ storage/ tmp/
chmod -R a+rX,u+w etc/ license/
chmod -R a-rwx,u+rwX log/ storage/ tmp/
