# Configuration 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection.config-service.grpc.port` | Number | False | The gRPC port of the server where the Config Service is running.<br />Default value: `null`. |
| `ataccama.client.connection.config-service.host` | String | False | The IP address or the URL of the server where the Config Service is running.<br />Default value: `null`. |
| `ataccama.client.grpc.properties.max-message-size` | String | False | The maximum size of gRPC message. KB are used if no unit is specified.<br />Default value: `1GB`. |
| `ataccama.config-service.heartbeat-interval` | Number | False | Defines the minimum amount of time after which the microservices signal to the Configuration Service that they are alive. Expressed in seconds.<br />Default value: `30`. |
| `ataccama.config-service.override-local` | Boolean | False | Defines whether the properties from the Configuration Service override the properties located in `etc/application.properties`. If set to `false`, priority is given to local properties. The property needs to be set in the Configuration Service, otherwise it is ignored.<br />Default value: `False`. |
| `ataccama.config-service.refresh-interval` | Number | False | Defines the minimum amount of time after which the microservices send a new request to retrieve properties from the Configuration Service. Expressed in seconds.<br />Default value: `30`. |
| `ataccama.one.aicore.artifact-version-txt.location` | String | False | The location of the `artifact-version.txt` containing resolved version of AI Core application.<br />Default value: `${ataccama.path.doc}/artifact-version.txt`. |
| `ataccama.one.aicore.config.etc-location` | String | False | The path to the `etc/application.properties` file.<br />Default value: `${ataccama.path.etc}/application.properties`. |
| `ataccama.one.aicore.config.location` | String | False | The location of the default `application.properties` file. The default value of this property can be overwritten only through environment variables, otherwise the change is ignored.<br />Default value: `${ataccama.path.lib}/application.properties`. |
| `ataccama.one.aicore.manage-py.location` | String | False | The path to the `manage.py` file, which is used to start microservices/processes of AI Core.<br />Default value: `${ataccama.path.lib}/manage.py`. |
| `ataccama.path.doc` | String | False | The location of the `doc` folder of the AI Core application.<br />Default value: `${ataccama.path.root}/doc`. |
| `ataccama.path.etc` | String | False | The location of the etc folder of the AI Core application. The `etc/application.properties` path is relative to this path. The default value of this property can be overwritten only through environment variables and the default `application.properties` file. Otherwise, the change is ignored, which can lead to unexpected behavior.<br />Default value: `${ataccama.path.root}/etc`. |
| `ataccama.path.lib` | String | False | The location of the `lib` folder of the AI Core application. The default `application.properties` path is relative to this path. The default value of this property can be overwritten only through environment variables, otherwise the change is ignored.<br />Default value: `${ataccama.path.root}/lib`. |
| `ataccama.path.log` | String | False | The location of the `log` folder of the AI Core application.<br />Default value: `${ataccama.path.root}/log`. |
| `ataccama.path.migrations` | String | False | The location of the `migrations` folder of the AI Core application.<br />Default value: `${ataccama.path.lib}/migrations`. |
| `ataccama.path.root` | String | False | The location of the root folder of the AI Core application. Some configuration paths are defined relatively to this path. The default value of this property can be overwritten only through environment variables, otherwise the change is ignored.<br />Default value: `.`. |
| `ataccama.path.tmp` | String | False | The location of the `tmp` folder of the AI Core application.<br />Default value: `${ataccama.path.root}/temp`. |

# Health 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.heartbeat_timeout` | Number | False | The timeout period during which the microservice and its subcomponents need to report as running, otherwise the whole microservice becomes unhealthy and its status changes to DOWN. The microservice also proactively shuts itself down when it registers such a situation.<br />Default value: `120`. |

# Logging 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.logging.json-console-appender` | Boolean | False | Enables JSON console appender. Only one console appender can be enabled at a time. |
| `ataccama.logging.json-file-appender` | Boolean | False | Enables JSON file appender. Only one file appender can be enabled at a time. |
| `ataccama.logging.plain-text-console-appender` | Boolean | False | Enables plain text console appender. Only one console appender can be enabled at a time. |
| `ataccama.logging.plain-text-file-appender` | Boolean | False | Enables plain text file appender. Only one file appender can be enabled at a time. |
| `ataccama.one.aicore.logging.compression` | String | False | A compression or archive format to which log files should be converted when they are closed.<br />Default value: `zip`. |
| `ataccama.one.aicore.logging.filename` | String | False | The name of the file used by the file appender.<br />Default value: `${ataccama.path.log}/aicore_{self.name}.log`. |
| `ataccama.one.aicore.logging.rotation` | String | False | Indicates how often the current log file should be closed and a new one started.<br />Default value: `4 days`. |
| `root.level` | String | False | The minimum severity level starting from which logged messages are sent to the sink.<br />Default value: `INFO`. |

# Retrying 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.retrying.stop.kwargs` | String | False | Controls retrying of gRPC and graphQL communication attempts. The property determines when retrying stops. By default, retrying stops after 6 attempts in total, out of which 5 are retries.<br />Default value: `{"max_attempt_number": 6}`. |
| `ataccama.one.aicore.retrying.stop.type` | String | False | Controls retrying of gRPC and graphQL communication attempts. The property determines which approach is used to stop retrying. For more information, see the [Tenacity API Reference](https://tenacity.readthedocs.io/en/latest/api.html), Stop Functions section.<br />Default value: `stop_after_attempt`. |
| `ataccama.one.aicore.retrying.wait.kwargs` | String | False | Controls retrying of gRPC and graphQL communication attempts. The property is used to calculate the duration of waiting periods between retries. For more information about how waiting periods between unsuccessful attempts are managed, see the [Tenacity API Reference](https://tenacity.readthedocs.io/en/latest/api.html), Wait Functions section.<br />Default value: `{"multiplier": 0.16, "exp_base": 2}`. |
| `ataccama.one.aicore.retrying.wait.type` | String | False | Controls retrying of gRPC and graphQL communication attempts. The property determines which approach is used when waiting. For more information about how waiting periods between unsuccessful attempts are managed, see the [Tenacity API Reference](https://tenacity.readthedocs.io/en/latest/api.html), Wait Functions section.<br />Default value: `wait_exponential`. |

# Wait for readiness on start 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.onstart.health.response-timeout` | Number | False | Sets for how many seconds the microservice waits after requesting health information about its dependencies, for example, when the Recommender waits for the Neighbors or the Autocomplete waits for MMM. For more information, see the [Requests Developer Interface Documentation](https://requests.readthedocs.io/en/master/api/), section about the `timeout` parameter.<br />Default value: `5`. |
| `ataccama.one.aicore.onstart.retrying.wait.kwargs` | String | False | Defines the behavior of the microservice while it waits on a dependency before starting. Keyword arguments (kwargs) are the arguments used to construct an instance of the specified wait type. In this case, the keyword argument sets the duration of waiting intervals.<br />Default value: `{"wait": 2.5}`. |
| `ataccama.one.aicore.onstart.retrying.wait.type` | String | False | Defines the behavior of the microservice while it waits on a dependency before starting. Currently, the microservice either waits to receive information about the health of the dependency or the database readiness (typically, this means waiting for the database to start and for MMM to create the tables needed). The property defines how waiting periods are managed between unsuccessful attempts to verify the readiness of the dependency. For a list of other available wait types, see the [Tenacity API Reference](https://tenacity.readthedocs.io/en/latest/api.html), Wait Functions section.<br />Default value: `wait_fixed`. |

# DB 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.database.connection` | String | False | Used to define the AI Core database connection configuration. Supported dialects: postgresql. Additional properties include the following: `ataccama.one.aicore.database.connection.dialect=postgres` `ataccama.one.aicore.database.connection.host=localhost:5432/ai` `ataccama.one.aicore.database.connection.username=one` `ataccama.one.aicore.database.connection.password=one`<br />Default value: `null`. |
| `ataccama.one.aicore.database.engine-kwargs` | String | False | Sets the SQLAlchemy engine options, such as the maximum length of identifiers used in the database. For more information, see the [Engine Configuration](https://docs.sqlalchemy.org/en/13/core/engines.html), section Engine Creation API, Parameters.<br />Default value: `{"max_identifier_length": 128}`. |
| `ataccama.one.aicore.database.poll-period` | Number | False | Defines how often the database is polled for changes. Used by the Term Suggestions microservice. Expressed in seconds.<br />Default value: `1`. |

# GraphQL 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.http.connect-timeout` | Number | False | Defines after which amount of time the HTTP call is ended if the socket does not receive any bytes. Expressed in seconds.<br />Default value: `5`. |

# MMM 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection.mmm.grpc.port` | Number | False | The gRPC port of the server where the MMM is running.<br />Default value: `8521`. |
| `ataccama.client.connection.mmm.host` | String | False | The IP address or the URL of the server where the MMM is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.mmm.http.port` | Number | False | The HTTP port of the server where the MMM is running.<br />Default value: `8021`. |

# Authentication - out 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.authentication.internal.jwt.generator.key` | String | False | The private key of the AI Core module used to generate tokens for internal JWT authentication. |
| `ataccama.authentication.internal.jwt.generator.token-expiration` | Number | False | Defines the amount of time after which the token generated by the internal JWT generator expires. Expressed in seconds.<br />Default value: `900`. |

# Parallelism 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.parallelism.blas` | Number | False | An alternative way of overriding the number of parallel threads spawned by low-level calculations that are used by machine learning algorithms. If the value is set to `0`, all CPU cores run without hyper-threads. If the value is not set (`null`), other properties are not overridden. Relies on the static OpenBLAS API and might be ignored depending on the compilation options for the OpenBLAS library. When this property is set, OpenBLAS gives it higher priority compared to `ataccama.one.aicore.parallelism.omp`. This is intended only for exceptional cases and should not be used otherwise.<br />Default value: `null`. |
| `ataccama.one.aicore.parallelism.jobs` | Number | False | The number of parallel threads or processes spawned by high-level machine learning algorithms with explicit job management. If the value is set to `0`, all CPU cores run without hyper-threads. If the value is not set (`null`), the library default settings are applied. Use this option together with `ataccama.one.aicore.parallelism.omp`. For more information, see the AI Core Sizing Guidelines.<br />Default value: `1`. |
| `ataccama.one.aicore.parallelism.omp` | Number | False | The number of parallel threads spawned by low-level calculations that are used by high-level machine learning algorithms. If the value is set to `0`, all CPU cores run without hyper-threads. If the value is not set (`null`), the library default settings are applied. The property relies on the static OpenBLAS API and OpenMP API, which have a lower overhead than the dynamic API used by the property `ataccama.one.aicore.parallelism.threads`. When this property is set, the OpenBLAS library gives it lower priority compared to `ataccama.one.aicore.parallelism.blas`. Several low-level libraries other than OpenBLAS and LAPACK, as well as libraries that use OpenMP, respect this option as well. Use this option together with `ataccama.one.aicore.parallelism.jobs`. For more information, see the AI Core Sizing Guidelines.<br />Default value: `1`. |
| `ataccama.one.aicore.parallelism.threads` | Number | False | An alternative way of setting the number of parallel threads spawned by low-level calculations that are used by machine learning algorithms. If the value is set to `0`, all CPU cores run without hyper-threads. If the value is not set (`null`), the dynamic API is not used. Relies on the dynamic OpenBLAS API, which has a higher overhead than the static API used by `ataccama.one.aicore.parallelism.omp`. When this property is set, OpenBLAS gives it higher priority compared to `ataccama.one.aicore.parallelism.omp` and `ataccama.one.aicore.parallelism.blas`. The dynamic API is intended only for exceptional cases and should not be used otherwise.<br />Default value: `null`. |

# TLS - out 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection` | String | False | All client TLS options can be specified per connection. To set any TLS option for a specific client connection, configure the same set of properties as for the global client TLS configuration (properties with the `ataccama.client.tls` prefix). Depending on your setup, use one of the following prefixes: `ataccama.client.connection.<connection_name>.tls` for specifying TLS for connections using any communication protocol (gRPC and HTTP), `ataccama.client.connection.<connection_name>.grpc.tls` for specifying TLS for connections using the gRPC communication protocol, `ataccama.client.connection.<connection_name>.http.tls` for specifying TLS for connections using the HTTP communication protocol. If an option is not specified for the given client connection, global client TLS options are applied.<br />Default value: `null`. |
| `ataccama.client.grpc.tls` | String | False | All client TLS options can be specified directly for gRPC client. To set any TLS option for a gRPC client, configure the same set of properties as for the global client TLS configuration (properties with the `ataccama.client.tls` prefix), but use the prefix `ataccama.client.grpc.tls` instead. If an option is not specified for the gRPC client, global client TLS options are applied.<br />Default value: `null`. |
| `ataccama.client.http.tls` | String | False | All client TLS options can be specified directly for HTTP client. To set any TLS option for a HTTP client, configure the same set of properties as for the global client TLS configuration (properties with the `ataccama.client.tls` prefix), but use the prefix `ataccama.client.http.tls` instead. If an option is not specified for the HTTP client, global client TLS options are applied.<br />Default value: `null`. |
| `ataccama.client.tls.enabled` | Boolean | False | Defines whether the gRPC and HTTP clients should use TLS when communicating with the servers.<br />Default value: `False`. |
| `ataccama.client.tls.key-alias` | String | False | The private key name specified in the provided keystore that is used for TLS. Does not work with `PKCS12` format. To avoid unexpected behavior, use `PKCS12` with only one private key.<br />Default value: `null`. |
| `ataccama.client.tls.key-password` | String | False | The password for the private key of the gRPC and HTTP clients. Used if the private key is encrypted. Does not work with `PKCS12` format. To avoid unexpected behavior, use `PKCS12` only with a non-encrypted private key.<br />Default value: `null`. |
| `ataccama.client.tls.key-store` | String | False | Points to the keystore containing private and public key certificates that are used by the gRPC and HTTP clients. For example, `file:${ataccama.path.etc}/key-store.pkcs12`.<br />Default value: `null`. |
| `ataccama.client.tls.key-store-password` | String | False | The password for the keystore. Used if the keystore is encrypted.<br />Default value: `null`. |
| `ataccama.client.tls.key-store-type` | String | False | The type of the keystore. Possible types are `PKCS12`, `JKS`, and `JCEKS`.<br />Default value: `null`. |
| `ataccama.client.tls.mtls` | Boolean | False | Defines whether the gRPC and HTTP clients should use mTLS when communicating with the servers.<br />Default value: `False`. |
| `ataccama.client.tls.trust-all` | Boolean | False | Defines whether the gRPC and HTTP clients should verify the certificate of the server with which they communicate.<br />Default value: `False`. |
| `ataccama.client.tls.trust-store` | String | False | Points to the truststore with all the trusted certification authorities (CAs) used in gRPC and HTTP TLS communication. Used only when `tls.trust-all` is disabled. For example, `file:${ataccama.path.etc}/trust-store.pkcs12`.<br />Default value: `null`. |
| `ataccama.client.tls.trust-store-password` | String | False | The password for the truststore. Used if the truststore is encrypted.<br />Default value: `null`. |
| `ataccama.client.tls.trust-store-type` | String | False | The type of the truststore. Possible types are `PKCS12` and `JCEKS`.<br />Default value: `null`. |

# Authentication - in 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.authentication.grpc.basic.enable` | Boolean | False | Enables basic authentication on the gRPC server. If enabled, Keycloak becomes a mandatory dependency - it needs to be running before the AI Core starts.<br />Default value: `True`. |
| `ataccama.authentication.grpc.bearer.enable` | Boolean | False | Enables bearer authentication on the gRPC server. If enabled, Keycloak becomes a mandatory dependency - it needs to be running before the AI Core starts.<br />Default value: `True`. |
| `ataccama.authentication.grpc.internal.jwt.enable` | Boolean | False | Enables internal JWT token authentication on the gRPC server.<br />Default value: `True`. |
| `ataccama.authentication.http.acl.default-allow` | Boolean | False | If set to `false`, nobody is allowed to access any HTTP endpoint. To explicitly allow access to some endpoint, access based on allowed roles can be configured via `ataccama.authentication.http.acl.endpoints`.<br />Default value: `True`. |
| `ataccama.authentication.http.acl.endpoints` | String | False | Used for securing HTTP endpoints based on user/module roles. The role comparison is case-insensitive. Example for allowing only `ADMIN` roles to access prometheus endpoint: `ataccama.authentication.http.acl.endpoints.prometheus-endpoint.endpoint-filter=["/actuator/prometheus"]`, `ataccama.authentication.http.acl.endpoints.prometheus-endpoint.allowed-roles=["ADMIN"].<br />Default value: `null`. |
| `ataccama.authentication.http.basic.enable` | Boolean | False | Enables basic authentication on the HTTP server. If enabled, Keycloak becomes a mandatory dependency - it needs to be running before the AI Core starts.<br />Default value: `True`. |
| `ataccama.authentication.http.basic.endpoint-filter` | String | False | Ant-style patterns that filter which HTTP endpoints have basic authentication enabled. Individual patterns are separated by `;`.<br />Default value: `/**`. |
| `ataccama.authentication.http.bearer.enable` | Boolean | False | Enables bearer authentication on the HTTP server. If enabled, Keycloak becomes a mandatory dependency - it needs to be running before the AI Core starts.<br />Default value: `True`. |
| `ataccama.authentication.http.bearer.endpoint-filter` | String | False | Ant-style patterns that filter which HTTP endpoints have bearer authentication enabled. Individual patterns are separated by `;`.<br />Default value: `/**`. |
| `ataccama.authentication.http.internal.jwt.enable` | Boolean | False | Enables internal JWT token authentication on the HTTP server.<br />Default value: `True`. |
| `ataccama.authentication.http.internal.jwt.endpoint-filter` | String | False | Ant-style patterns that filter which HTTP endpoints have internal JWT authentication enabled. Individual patterns are separated by `;`.<br />Default value: `/**`. |
| `ataccama.authentication.http.public-endpoint-restriction-filter` | String | False | Ant-style patterns that filter which public HTTP endpoints should be protected. These endpoint become no longer public and authentication is required. Individual patterns are separated by `;`.<br />Default value: `null`. |
| `ataccama.authentication.internal.jwt.impersonation-role` | String | False | Role used for validating that service that sends request to AI Core can impersonate a user.<br />Default value: `IMPERSONATION`. |
| `ataccama.authentication.keycloak.realm` | String | False | The name of the Keycloak realm. Used when requesting an access token during authorization. |
| `ataccama.authentication.keycloak.server-url` | String | False | The URL of the server where Keycloak is running. |
| `ataccama.authentication.keycloak.token.audience` | String | False | The expected recipients of the Keycloak token. Used to validate the access (bearer) token obtained from Keycloak. If the value is `null`, the audience is not verified.<br />Default value: `null`. |
| `ataccama.authentication.keycloak.token.client-id` | String | False | The client token identifier of the AI Core module. Used when requesting an access token during authorization. |
| `ataccama.authentication.keycloak.token.expected-algorithm` | String | False | The expected algorithm that was used to sign the access (bearer) token obtained from Keycloak.<br />Default value: `RS256`. |
| `ataccama.authentication.keycloak.token.issuer` | String | False | The issuer of the Keycloak token. Used to validate the access (bearer) token obtained from Keycloak. If the value is `null`, the issuer is not verified.<br />Default value: `${ataccama.authentication.keycloak.server-url}/realms/${ataccama.authentication.keycloak.realm}`. |
| `ataccama.authentication.keycloak.token.key-cache-min-time-between-request` | Number | False | Defines the minimum amount of time between two consecutive requests for Keycloak certificates during which Keycloak is not asked for new certificates. This acts as a prevention against DDoS attacks with an unknown key. Expressed in seconds.<br />Default value: `5`. |
| `ataccama.authentication.keycloak.token.key-cache-ttl` | Number | False | Defines how long the public certificates from Keycloak are cached on the AI Core side. If this time is exceeded, new certificates are fetched from Keycloak before the AI Core makes an attempt to authenticate. If this time is not exceeded, but the public certificate for the key parsed from the authentication attempt was not found in the cache, new certificates are fetched from Keycloak and authentication is attempted again. Expressed in seconds.<br />Default value: `300`. |
| `ataccama.authentication.keycloak.token.secret` | String | False | The secret key of the AI Core client. Used when requesting an access token during authorization. |
| `ataccama.one.platform.deployments` | String | True | Deployment settings (with public JWT keys) for other modules communicating with AI Core. Required fields for deployment are: `module`, `uri`, `roles`. These fields are used for creation of service identity during authentication. Required fields for JWT key are: `fingerprint`, `content`. Optional `is-revoked` is used for revoking the corresponding JWT key (e.g. via Config Service) if the key was compromised. Example settings for MMM: `ataccama.one.platform.deployments.mmm-be.module=<value>`, `ataccama.one.platform.deployments.mmm-be.uri=<value>`, `ataccama.one.platform.deployments.mmm-be.security.roles=<value>`, `ataccama.one.platform.deployments.mmm-be.security.jwt-keys.mmm-key.fingerprint=<value>`, `ataccama.one.platform.deployments.mmm-be.security.jwt-keys.mmm-key.content=<value>`, `ataccama.one.platform.deployments.mmm-be.security.jwt-keys.mmm-key.is-revoked=false`.<br />Default value: `null`. |

# Encryption 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `internal.encryption.key-store` | String | False | Points to the keystore containing private and public key certificates that are used by the gRPC and HTTP clients. For example, `file:${ataccama.path.etc}/key-store.pkcs12`.<br />Default value: `null`. |
| `internal.encryption.key-store-password` | String | False | The password for the keystore. Used if the keystore is encrypted.<br />Default value: `null`. |
| `internal.encryption.key-store-type` | String | False | The type of the keystore. Possible types are `PKCS12`, `JKS`, and `JCEKS`.<br />Default value: `null`. |
| `properties.encryption.key-store` | String | False | Points to the keystore containing private and public key certificates that are used by the gRPC and HTTP clients. For example, `file:${ataccama.path.etc}/key-store.pkcs12`.<br />Default value: `null`. |
| `properties.encryption.key-store-password` | String | False | The password for the keystore. Used if the keystore is encrypted.<br />Default value: `null`. |
| `properties.encryption.key-store-type` | String | False | The type of the keystore. Possible types are `PKCS12`, `JKS`, and `JCEKS`.<br />Default value: `null`. |

# TLS - in 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.server.grpc.tls` | String | False | All server TLS options can be specified directly for gRPC server. To set any TLS option for a gRPC server, configure the same set of properties as for the global server TLS configuration (properties with the `ataccama.server.tls` prefix), but use the prefix `ataccama.server.grpc.tls` instead. If an option is not specified for the gRPC server, global server TLS options are applied.<br />Default value: `null`. |
| `ataccama.server.http.tls` | String | False | All server TLS options can be specified directly for HTTP server. To set any TLS option for a HTTP server, configure the same set of properties as for the global server TLS configuration (properties with the `ataccama.server.tls` prefix), but use the prefix `ataccama.server.http.tls` instead. If an option is not specified for the HTTP server, global server TLS options are applied.<br />Default value: `null`. |
| `ataccama.server.tls.allow-generate` | Boolean | False | Defines whether the gRPC and HTTP servers should generate their self-signed certificate. The private key is saved to a location specified by `ataccama.server.tls.private-key` and the certificate to a location specified by `ataccama.server.tls.cert-chain`.<br />Default value: `False`. |
| `ataccama.server.tls.cert-chain` | String | False | The path to the generated certificate of the gRPC and HTTP servers. For example, `file:${ataccama.path.etc}/server.crt`.<br />Default value: `null`. |
| `ataccama.server.tls.enabled` | Boolean | False | Defines whether the gRPC and HTTP servers should use TLS authentication.<br />Default value: `False`. |
| `ataccama.server.tls.key-alias` | String | False | The private key name specified in the provided keystore that is used for TLS. Does not work with `PKCS12` format. To avoid unexpected behavior, use `PKCS12` with only one private key.<br />Default value: `null`. |
| `ataccama.server.tls.key-password` | String | False | The password for the private key of the gRPC and HTTP servers. Used if the private key is encrypted." Does not work with `PKCS12` format. To avoid unexpected behavior, use `PKCS12` only with a non-encrypted private key.<br />Default value: `null`. |
| `ataccama.server.tls.key-store` | String | False | Points to the keystore containing private and public key certificates that are used by the gRPC and HTTP servers. For example, `file:${ataccama.path.etc}/key-store.pkcs12`.<br />Default value: `null`. |
| `ataccama.server.tls.key-store-password` | String | False | The password for the keystore. Used if the keystore is encrypted.<br />Default value: `null`. |
| `ataccama.server.tls.key-store-type` | String | False | The type of the keystore. Possible types are `PKCS12`, `JKS`, and `JCEKS`.<br />Default value: `null`. |
| `ataccama.server.tls.mtls` | String | False | Defines whether the gRPC and HTTP servers require clients to be authenticated. Possible values are `NONE`, `OPTIONAL`, `REQUIRED`. Can be set to `REQUIRED` only if `ataccama.server.tls.trust-cert-collection` is specified as well.<br />Default value: `OPTIONAL`. |
| `ataccama.server.tls.private-key` | String | False | The path to the generated private key of the gRPC and HTTP servers. For example, `file:${ataccama.path.etc}/server.key`.<br />Default value: `null`. |
| `ataccama.server.tls.trust-store` | String | False | Points to the truststore with all the trusted certification authorities (CAs) used in the gRPC and HTTP TLS communication. For example, `file:${ataccama.path.etc}/trust-store.pkcs12`.<br />Default value: `null`. |
| `ataccama.server.tls.trust-store-password` | String | False | The password for the truststore. Used if the truststore is encrypted.<br />Default value: `null`. |
| `ataccama.server.tls.trust-store-type` | String | False | The type of the truststore. Possible types are `PKCS12` and `JCEKS`.<br />Default value: `null`. |

# Security headers 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.security.header.Strict-Transport-Security` | String | False | The value of the HTTP Strict-Transport-Security (HSTS) response header. Used only when HTTPS is enabled. Informs browsers that the resource should only be accessed using the HTTPS protocol.<br />Default value: `max-age=31536000; includeSubDomains; preload`. |

# Supervisor 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.supervisor.captured-microservices` | String | False | A list of microservices whose stdout and stderr streams are forwarded to the respective stdout and stderr streams of the Supervisor process for debugging purposes.<br />Default value: `[]`. |
| `ataccama.one.aicore.supervisor.http.server.listen-address` | String | False | The network address to which the Supervisor HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.supervisor.http.server.port` | Number | False | The HTTP port where the Supervisor microservice is running.<br />Default value: `8040`. |
| `ataccama.one.aicore.supervisor.liveness.connection-timeout` | Number | False | When the Supervisor runs a health check, this property controls for how long the Supervisor waits to receive data before cancelling the request. If the connection times out, the microservice is considered as no longer running. For more information, see the [Requests Developer Interface Documentation](https://requests.readthedocs.io/en/master/api/), section about the `timeout` parameter.<br />Default value: `5`. |
| `ataccama.one.aicore.supervisor.liveness.interval` | Number | False | Determines how often a health check is performed. By default, this is done once every minute. Expressed in seconds.<br />Default value: `60`. |
| `ataccama.one.aicore.supervisor.liveness.retries` | Number | False | Determines how many consecutive health checks need to fail, indicating that the microservice is no longer running, before the microservice is restarted.<br />Default value: `3`. |
| `ataccama.one.aicore.supervisor.liveness.start-delay` | Number | False | Defines for how long the Supervisor waits after starting a microservice before it starts checking its health (a temporary workaround). Expressed in seconds.<br />Default value: `10`. |
| `ataccama.one.aicore.supervisor.microservices` | String | False | Defines which microservices are started when the Supervisor is run.<br />Default value: `["matching_manager", "anomaly_detector", "translator", "autocomplete", "spellchecker", "recommender", "neighbors", "feedback", "upgrade"]`. |
| `ataccama.one.aicore.supervisor.shutdown-timeout` | Number | False | When the Supervisor is asked to shut down (for example, by pressing `Ctrl+C`), the service asks the microservices to shut down as well. This property defines how much time the microservices have to gracefully shut down before they are stopped.<br />Default value: `5`. |

# Term suggestions 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection.feedback.host` | String | False | The IP address or the URL of the server where the Feedback microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.feedback.http.port` | Number | False | The HTTP port of the server where the Feedback microservice is running.<br />Default value: `8043`. |
| `ataccama.client.connection.neighbors.grpc.port` | Number | False | The gRPC port of the server where the Neighbors microservice is running.<br />Default value: `8542`. |
| `ataccama.client.connection.neighbors.host` | String | False | The IP address or the URL of the server where the Neighbors microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.neighbors.http.port` | Number | False | The HTTP port of the server where the Neighbors microservice is running.<br />Default value: `8042`. |
| `ataccama.client.connection.recommender.host` | String | False | The IP address or the URL of the server where the Recommender microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.recommender.http.port` | Number | False | The HTTP port of the server where the Recommender microservice is running.<br />Default value: `8041`. |
| `ataccama.one.aicore.term-suggestions.feedback.batch-size` | Number | False | The number of feedbacks for which thresholds are recomputed at once by the Feedback service. If the batch size is too small, the database is queried too often and the computation is inefficient. If the batch size is too large, the Feedback service can in turn require more memory resources.<br />Default value: `10000`. |
| `ataccama.one.aicore.term-suggestions.feedback.grpc.server.listen-address` | String | False | The network address to which the Feedback gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.term-suggestions.feedback.grpc.server.port` | Number | False | The port where the gRPC interface of the Feedback microservice is running.<br />Default value: `8543`. |
| `ataccama.one.aicore.term-suggestions.feedback.http.server.listen-address` | String | False | The network address to which the Feedback HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.term-suggestions.feedback.http.server.port` | Number | False | The HTTP port where the Feedback microservice is running.<br />Default value: `8043`. |
| `ataccama.one.aicore.term-suggestions.neighbors.cache.attributes-limit` | Number | False | The maximum number of fingerprints that can be present in the index used for searching neighbors. Once this value is reached, the microservice shuts down when trying to add new attributes. If the number of attributes in the database, including the deleted ones, exceeds the limit on startup, the microservice waits in the Not ready state indefinitely or until the number of attributes is reduced to this value or lower.<br />Default value: `1000000`. |
| `ataccama.one.aicore.term-suggestions.neighbors.grpc.server.listen-address` | String | False | The network address to which the Neighbors gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.term-suggestions.neighbors.grpc.server.port` | Number | False | The port where the gRPC interface of the Neighbors microservice is running.<br />Default value: `8542`. |
| `ataccama.one.aicore.term-suggestions.neighbors.http.server.listen-address` | String | False | The network address to which the Neighbors HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.term-suggestions.neighbors.http.server.port` | Number | False | The HTTP port where the Neighbors microservice is running.<br />Default value: `8042`. |
| `ataccama.one.aicore.term-suggestions.recommender.batch-size` | Number | False | The number of attributes for which term suggestions are recomputed at once by the Recommender service. If the batch size is too small, the database is queried too often and the computation is inefficient. If the batch size is too large, the process can take a long time, which in turn can render the Recommender unresponsive for the duration of the request and require more memory resources.<br />Default value: `1000`. |
| `ataccama.one.aicore.term-suggestions.recommender.default-threshold` | Number | False | The default starting distance threshold for newly created terms. The distance threshold defines how close the fingerprints need to be so that, if one of them has some terms assigned, the AI Core suggests those terms to the other one as well. It also affects the confidence of suggestions.<br />Default value: `1.0`. |
| `ataccama.one.aicore.term-suggestions.recommender.grpc.server.listen-address` | String | False | The network address to which the Recommender gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.term-suggestions.recommender.grpc.server.port` | Number | False | The port where the gRPC interface of the Recommender microservice is running.<br />Default value: `8541`. |
| `ataccama.one.aicore.term-suggestions.recommender.http.server.listen-address` | String | False | The network address to which the Recommender HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.term-suggestions.recommender.http.server.port` | Number | False | The HTTP port where the Recommender microservice is running.<br />Default value: `8041`. |
| `ataccama.one.aicore.term-suggestions.recommender.max-threshold` | Number | False | Sets the highest possible value for the similarity threshold (see the `recommender.target-accuracy` property). This value cannot be surpassed even when users consistently accept all term suggestions, which results in the AI Core attempting to further expand the threshold in order to lower the acceptance rate and meet the target accuracy.<br />Default value: `16`. |
| `ataccama.one.aicore.term-suggestions.recommender.target-accuracy` | Number | False | The target ratio of term suggestions that users approved to the total number of suggestions, both approved and rejected, that the AI Core is trying to achieve. This is done by slowly adapting the similarity threshold for each term over time.<br />Default value: `0.8`. |
| `ataccama.one.aicore.term-suggestions.recommender.threshold-step` | Number | False | The speed at which the similarity threshold is adapted. The similarity threshold has a role in reaching the set `recommender.target-accuracy`.<br />Default value: `0.1`. |
| `ataccama.server.grpc.properties.max-message-size` | String | False | The maximum size of gRPC message. KB are used if no unit is specified.<br />Default value: `1GB`. |

# NLP search 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection.autocomplete.grpc.port` | Number | False | The gRPC port of the server where the Autocomplete microservice is running.<br />Default value: `8545`. |
| `ataccama.client.connection.autocomplete.host` | String | False | The IP address or the URL of the server where the Autocomplete microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.autocomplete.http.port` | Number | False | The HTTP port of the server where the Autocomplete microservice is running.<br />Default value: `8045`. |
| `ataccama.client.connection.spellchecker.grpc.port` | Number | False | The gRPC port of the server where the Spellchecker microservice is running.<br />Default value: `8544`. |
| `ataccama.client.connection.spellchecker.host` | String | False | The IP address or the URL of the server where the Spellchecker microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.spellchecker.http.port` | Number | False | The HTTP port of the server where the Spellchecker microservice is running.<br />Default value: `8044`. |
| `ataccama.client.connection.translator.grpc.port` | Number | False | The gRPC port of the server where the Translator microservice is running.<br />Default value: `8546`. |
| `ataccama.client.connection.translator.host` | String | False | The IP address or the URL of the server where the Translator microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.translator.http.port` | Number | False | The HTTP port of the server where the Translator microservice is running.<br />Default value: `8046`. |
| `ataccama.one.aicore.nlp-search.autocomplete.grpc.server.listen-address` | String | False | The network address to which the Autocomplete gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.nlp-search.autocomplete.grpc.server.port` | Number | False | The port where the gRPC interface of the Autocomplete microservice is running.<br />Default value: `8545`. |
| `ataccama.one.aicore.nlp-search.autocomplete.http.server.listen-address` | String | False | The network address to which the Autocomplete HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.nlp-search.autocomplete.http.server.port` | Number | False | The HTTP port where the Autocomplete microservice is running.<br />Default value: `8045`. |
| `ataccama.one.aicore.nlp-search.nodes-to-request` | String | True | A JSON definition of the relation between search template placeholders and entity types.<br />Default value: `[{"placeholder_value": "source", "entity_request": "sources"}, {"placeholder_value": "term", "entity_request": "terms"}]`. |
| `ataccama.one.aicore.nlp-search.query-parts-config` | String | True | A JSON definition of search suggestions templates.<br />Default value: `{"with term": {"value": "term", "AQL": {"catalogItem": "(termInstances.some(target{name like ${term} OR synonym like ${term} OR abbreviation like ${term}}) OR attributes.some(termInstances.some(target{name like ${term} OR synonym like ${term} OR abbreviation like ${term}})))", "source": "locations.some(catalogItems.some(termInstances.some(target{name like ${term}}))) OR locations.some(locations.some(catalogItems.some(termInstances.some(target{name like ${term}}))))"}, "allow_negations": true}, "from source": {"value": "source", "AQL": {"catalogItem": "($parent.$parent.name like ${source} OR $parent.$parent.$parent.name like ${source} OR $parent.$parent.$parent.$parent.name like ${source})"}, "allow_negations": true}, "with attribute": {"value": "attribute", "AQL": {"catalogItem": "attributes.some(name like ${attribute})"}, "allow_negations": true}, "fulltext": {"value": "anything", "AQL": {"all": "$fulltext like ${anything}"}}}`. |
| `ataccama.one.aicore.nlp-search.request-metadata-period-s` | Number | False | Defines how often requests are sent to MMM to retrieve metadata entity names, such as names of terms and sources, which are used for autocomplete.<br />Default value: `60`. |
| `ataccama.one.aicore.nlp-search.spellchecker.grpc.server.listen-address` | String | False | The network address to which the Spellchecker gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.nlp-search.spellchecker.grpc.server.port` | Number | False | The port where the gRPC interface of the Spellchecker microservice is running.<br />Default value: `8544`. |
| `ataccama.one.aicore.nlp-search.spellchecker.http.server.listen-address` | String | False | The network address to which the Spellchecker HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.nlp-search.spellchecker.http.server.port` | Number | False | The HTTP port where the Spellchecker microservice is running.<br />Default value: `8044`. |
| `ataccama.one.aicore.nlp-search.spellchecker.languages` | String | False | A list of languages used for AQL error checking. For every stated language, a file named `<language_name>_word_frequencies.txt` is searched for in the vocabularies folder.<br />Default value: `["english"]`. |
| `ataccama.one.aicore.nlp-search.spellchecker.vocabularies-folder` | String | False | Points to the location of vocabularies used for AQL error checking.<br />Default value: `${ataccama.path.etc}/data/nlp_search`. |
| `ataccama.one.aicore.nlp-search.translator.grpc.server.listen-address` | String | False | The network address to which the Translator gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.nlp-search.translator.grpc.server.port` | Number | False | The port where the gRPC interface of the Translator microservice is running.<br />Default value: `8546`. |
| `ataccama.one.aicore.nlp-search.translator.http.server.listen-address` | String | False | The network address to which the Translator HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.nlp-search.translator.http.server.port` | Number | False | The HTTP port where the Translator microservice is running.<br />Default value: `8046`. |

# Anomaly detection 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection.anomaly-detector.host` | String | False | The IP address or the URL of the server where the Anomaly Detector microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.anomaly-detector.http.port` | Number | False | The HTTP port of the server where the Anomaly Detector microservice is running.<br />Default value: `8047`. |
| `ataccama.one.aicore.anomaly-detection.anomaly-detector.grpc.server.listen-address` | String | False | The network address to which the Anomaly Detector gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.anomaly-detection.anomaly-detector.grpc.server.port` | Number | False | The port where the gRPC interface of the Anomaly Detector microservice is running.<br />Default value: `8547`. |
| `ataccama.one.aicore.anomaly-detection.anomaly-detector.http.server.listen-address` | String | False | The network address to which the Anomaly Detector HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.anomaly-detection.anomaly-detector.http.server.port` | Number | False | The HTTP port where the Anomaly Detector microservice is running.<br />Default value: `8047`. |
| `ataccama.one.aicore.anomaly-detection.anomaly-detector.isolation-forest-threshold` | Number | False | An internal parameter for the time-independent anomaly detection model (Isolation Forest) that defines the sensitivity of anomaly detection. Setting the value higher than the default value (for example, -0.5) can result in more false positive anomalies, while setting it lower than the default value (for example, -0.7) can lead to more false negative anomalies.<br />Default value: `-0.6`. |
| `ataccama.one.aicore.anomaly-detection.anomaly-detector.max-history-length` | Number | False | The maximum number of catalog item profile versions fetched from MMM on which anomaly detection is run. If the total number of profile versions in MMM exceeds the value set for this property, the versions are retrieved starting from the most recent. For example, if there are 30 profile versions in MMM and the property is set to 100, all 30 versions are fetched. However, if there are 200 profile versions in MMM and the value provided is 100, the last 100 profile versions are retrieved.<br />Default value: `100`. |
| `ataccama.one.aicore.anomaly-detection.anomaly-detector.time-series-std-threshold` | Number | False | An internal parameter for the time-dependent anomaly detection model (time series analysis) that defines the sensitivity of anomaly detection. The property describes the number of standard deviations (std) from the mean after which a point is considered as anomalous. Setting the value higher than the default value (for example, 4) reduces the total number of anomalies and results in more false negative anomalies, while setting it lower than the default value (for example, 2) increases the total number of detected anomalies and results in more false positive anomalies.<br />Default value: `3.0`. |

# AI Matching 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection.matching-manager.grpc.port` | Number | False | The gRPC port of the server where the Matching Manager microservice is running.<br />Default value: `8640`. |
| `ataccama.client.connection.matching-manager.host` | String | False | The IP address or the URL of the server where the Matching Manager microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.matching-manager.http.port` | Number | False | The HTTP port of the server where the Matching Manager microservice is running.<br />Default value: `8140`. |
| `ataccama.client.connection.mdc.grpc.port` | Number | False | The gRPC port of the server where the MDC is running.<br />Default value: `18581`. |
| `ataccama.client.connection.mdc.host` | String | False | The IP address or the URL of the server where the MDC is running.<br />Default value: `localhost`. |
| `ataccama.one.aicore.ai-matching.matching-manager.grpc.server.listen-address` | String | False | The network address to which the Matching Manager gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.ai-matching.matching-manager.grpc.server.port` | Number | False | The port where the gRPC interface of the Matching Manager microservice is running.<br />Default value: `8640`. |
| `ataccama.one.aicore.ai-matching.matching-manager.http.server.listen-address` | String | False | The network address to which the Matching Manager HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.ai-matching.matching-manager.http.server.port` | Number | False | The HTTP port where the Matching Manager microservice is running.<br />Default value: `8140`. |
| `ataccama.one.aicore.ai-matching.matching_steps.clustering.decision_threshold` | Number | False | The dedupe clustering decision threshold that functions as a compromise between precision and recall. The value needs to be between `0` and `1`. Increasing the value means a higher precision and lower recall, that is, fewer `MERGE` proposals and more `SPLIT` proposals. Inversely, decreasing the value results in a lower level of precision and higher recall.<br />Default value: `0.5`. |
| `ataccama.one.aicore.ai-matching.matching_steps.evaluation.groups_fetching_batch_size` | Number | False | The number of groups or clusters that are processed in a single batch when proposals are generated during the AI Matching evaluation. A higher number means that the processing is more efficient but requires more memory (RAM).<br />Default value: `100`. |
| `ataccama.one.aicore.ai-matching.matching_steps.evaluation.scoring_batch_size` | Number | False | The number of proposals that are processed in a single batch when proposals are scored during the AI Matching evaluation. A higher number means that the processing is more efficient but requires more memory (RAM).<br />Default value: `5000`. |
| `ataccama.one.aicore.ai-matching.matching_steps.initialization.sample_size` | Number | False | The number of records that are uniformly sampled from all the records fetched from MDM. Those records are the only ones used for initializing and training the AI Matching model.<br />Default value: `1000000`. |
| `ataccama.one.aicore.ai-matching.matching_steps.initialization.training_sample_size` | Number | False | The number of records that the AI Matching selects out of the records covered by the property `ai-matching.matching_steps.initialization.sample_size` for the actual training of the AI model. A higher value means that the model performs better, but the training takes more time.<br />Default value: `40000`. |
| `ataccama.one.aicore.ai-matching.matching_steps.rules_extraction.max_columns` | Number | False | The maximum number of columns in one extracted rule. A higher number means that the extracted rules can be more complex, that is, use more columns, but the rule extraction might take significantly longer.<br />Default value: `5`. |

# Migration 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection.upgrade.host` | String | False | The IP address or the URL of the server where the Upgrade microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.upgrade.http.port` | Number | False | The HTTP port of the server where the Upgrade microservice is running.<br />Default value: `8141`. |
| `ataccama.one.aicore.migration.upgrade.http.server.listen-address` | String | False | The network address to which the Upgrade HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.migration.upgrade.http.server.port` | Number | False | The HTTP port where the Upgrade microservice is running.<br />Default value: `8141`. |

# Metadata fetching 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.metadata-fetcher.dump-method` | String | False | Defines the method of creating the metadata dump output. Possible values: `s3`, `fs`.<br />Default value: `s3`. |
| `ataccama.one.aicore.metadata-fetcher.fetched-entities` | String | False | A list of entity types defining entity instances which should be fetched from MMM. Empty list means all entity types. If not empty, all entity types from the list and all entity types reachable from this list by properties defined in ataccama.one.aicore.metadata-fetcher.traversed_properties will be fetched.<br />Default value: `["catalogItem"]`. |
| `ataccama.one.aicore.metadata-fetcher.fs.dump-path` | String | False | File path of the metadata dump in the file system.<br />Default value: `metadata.json`. |
| `ataccama.one.aicore.metadata-fetcher.s3.bucket` | String | False | Name of a bucket in the S3 service to dump the metadata into.<br />Default value: `null`. |
| `ataccama.one.aicore.metadata-fetcher.s3.credentials.access-key` | String | False | Access key (aka user ID) of an account in S3 service.<br />Default value: `null`. |
| `ataccama.one.aicore.metadata-fetcher.s3.credentials.secret-key` | String | False | Secret Key (aka password) of an account in S3 service.<br />Default value: `null`. |
| `ataccama.one.aicore.metadata-fetcher.s3.dump-path` | String | False | File path of the metadata dump in the S3 bucket.<br />Default value: `metadata.json`. |
| `ataccama.one.aicore.metadata-fetcher.s3.endpoint` | String | False | S3 endpoint used to dump the metadata.<br />Default value: `null`. |
| `ataccama.one.aicore.metadata-fetcher.s3.region` | String | False | Region name of a bucket in S3 service.<br />Default value: `null`. |
| `ataccama.one.aicore.metadata-fetcher.s3.sse.enabled` | Boolean | False | Defines whether the Server-Side Encryption with Amazon S3-Managed Keys (SSE-S3) is used.<br />Default value: `True`. |
| `ataccama.one.aicore.metadata-fetcher.s3.tls.enabled` | Boolean | False | Defines whether the minio client should use TLS when communicating with the S3 service.<br />Default value: `True`. |
| `ataccama.one.aicore.metadata-fetcher.traversed-properties` | String | False | A list of properties which will be used to traverse the meta-metadata structure to determine entity types to fetch - see ataccama.one.aicore.metadata-fetcher.fetched_entities. Possible values are: "SE" (Single embedded), "AE" (Array embedded), "SR" (Single reference).<br />Default value: `["SE", "AE"]`. |

# CLI Client 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.client.connection.cli-client.host` | String | False | The IP address or the URL of the server where the CLI Client microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.cli-client.http.port` | Number | False | The HTTP port of the server where the CLI Client microservice is running.<br />Default value: `9041`. |
| `ataccama.client.connection.cli-graphql.host` | String | False | The IP address or the URL of the server where the CLI GraphQL is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.cli-graphql.http.port` | Number | False | The HTTP port of the server where the CLI GraphQL is running.<br />Default value: `8021`. |
| `ataccama.client.connection.cli-server.grpc.port` | Number | False | The gRPC port of the server where the CLI Server microservice is running.<br />Default value: `9540`. |
| `ataccama.client.connection.cli-server.host` | String | False | The IP address or the URL of the server where the CLI Server microservice is running.<br />Default value: `localhost`. |
| `ataccama.client.connection.cli-server.http.port` | Number | False | The HTTP port of the server where the CLI Server microservice is running.<br />Default value: `9040`. |
| `ataccama.one.aicore.cli-client.http.server.listen-address` | String | False | The network address to which the CLI Client HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.cli-client.http.server.port` | Number | False | The HTTP port where the CLI Client microservice is running.<br />Default value: `9041`. |

# CLI Server 
| Property    | Data Type   | Refreshable | Description |
| ----------- | ----------- | ----------- | ----------- |
| `ataccama.one.aicore.cli-server.grpc.server.listen-address` | String | False | The network address to which the CLI Server gRPC server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.cli-server.grpc.server.port` | Number | False | The port where the gRPC interface of the CLI Server microservice is running.<br />Default value: `9540`. |
| `ataccama.one.aicore.cli-server.http.server.listen-address` | String | False | The network address to which the CLI Server HTTP server should bind.<br />Default value: `0.0.0.0`. |
| `ataccama.one.aicore.cli-server.http.server.port` | Number | False | The HTTP port where the CLI Server microservice is running.<br />Default value: `9040`. |
