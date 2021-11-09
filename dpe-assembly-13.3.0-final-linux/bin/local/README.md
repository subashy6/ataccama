# Local launch script

This directory contains `exec_local.sh` file that can be used to customize the launch of the new jobs processes running locally.

Note that the shell script is not used by default. If you want to use the shell script change the property `plugin.executor-launch-model.launchTypeProperties.LOCAL.exec` in `application.properties`.

Example:
```properties
plugin.executor-launch-model.ataccama.one.launch-type-properties.LOCAL.exec=${ataccama.path.root}/bin/local/exec_local.sh
```
