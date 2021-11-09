# Application properties

There are several application properties in the directory.

* `application.properties` - Standard application properties containing all the basic properties.
* `docker.properties` - Application properties used in docker. It will be used instead of application.properties file.
* `application-SPARK_DATABRICKS.properties` - Configures **SPARK_DATABRICKS** profile that contains properties for the configuration of Spark via Databricks. The profile is mutually exclusive with **SPARK_HADOOP** profile.
* `application-SPARK_HADOOP.properties` - Configures **SPARK_HADOOP** profile that contains properties for the configuration of Spark running on Hadoop cluster. The profile is not available on linux operating system. The profile is mutually exclusive with **SPARK_DATABRICKS** profile.

The profiles are not enabled by default. It is necessary to turn them on in `application.properties` file.

Example:
```properties
# The following line enables SPARK_HADOOP profile.
spring.profiles.active=SPARK_HADOOP
```
