# Changelog
Each released version should contain information about changes done in that version.
For the sake of clarity, description of a change can be done in more than one sentence.
Each change should have a link to corresponding Jira issue.
The format should adhere to the following template:

## X.Y.Z (release version)

### New and Newsworthy
New features, general improvements and changes, config changes...

### Stability Improvements
New versions of 3rd party dependencies, handling of previously not known errors... 

### Performance Improvements
Faster algorithms, lower memory consumption...

### Observability Improvements
Better error reporting, new metrics, new logging messages, reporting utilities improving troubleshooting...


## 13.3.0
### New and Newsworthy
* Improve processing frequencies in Anomaly detection, using row and distinct counts. [ONE-23231](https://support.ataccama.com/jira/browse/ONE-23231)
* Fix of Anomaly detection bug in number imprecision in expected bound in time series analysis [ONE-24616](https://support.ataccama.com/jira/browse/ONE-24616)
* Added job for fetching metadata from MMM. [ONE-22790](https://support.ataccama.com/jira/browse/ONE-22790), [ONE-24223](https://support.ataccama.com/jira/browse/ONE-24223)

### Stability Improvements
* Updated following 3rd party dependencies:
  * jwcrypto to v0.9.1
  * minio to v7.0.4
  * psycopg2-binary to v2.9.1
  * pyjwt to v2.1.0 [ONE-23251](https://support.ataccama.com/jira/browse/ONE-23251)
  * scipy to v1.7.0
  * sqlalchemy to v1.4.18

### Performance Improvements
* Removed unnecessary package imports (reduced consumed memory). [ONE-5131](https://support.ataccama.com/jira/browse/ONE-5131)

### Observability Improvements
* Logging info about Config Service gRPC connection failure/re-establishment. [ONE-23346](https://support.ataccama.com/jira/browse/ONE-23346)
* Better handling of invalid response codes and processing errors when submitting GraphQL requests. [ONE-23880](https://support.ataccama.com/jira/browse/ONE-23880)
* Logging authentication failure reason for GraphQL requests. [ONE-24494](https://support.ataccama.com/jira/browse/ONE-24494)
* Removed `wsgi_application` logging for successful requests to monitoring endpoint. [ONE-5131](https://support.ataccama.com/jira/browse/ONE-5131)
* Unified metrics names. [ONE-5135](https://support.ataccama.com/jira/browse/ONE-5135)

## 13.2.0
### Added
* Upgrade microservice for running DB upgrades ([ONE-22615](https://support.ataccama.com/jira/browse/ONE-22615))
* Metadata fetcher job PoC [ONE-23151](https://support.ataccama.com/jira/browse/ONE-23151)
* Neighbors metrics for better monitoring of index occupancy/capacity vs number of attributes available in the DB [ONE-23331](https://support.ataccama.com/jira/browse/ONE-23331)
* Limit for neighbors fingerprint index size [ONE-23329](https://support.ataccama.com/jira/browse/ONE-23329)
* Pre-allocate memory for fingerprints in neighbors on start [ONE-19661](https://support.ataccama.com/jira/browse/ONE-19661)
* Human-facing health-check for checking microservice state [ONE-22087](https://support.ataccama.com/jira/browse/ONE-22087)

### Changed
* Upgraded to Python 3.9.5 [ONE-23018](https://support.ataccama.com/jira/browse/ONE-23018)
* Substitute [scikit-learn](https://scikit-learn.org/stable/) by [FAISS](https://ai.facebook.com/tools/faiss/) for nearest neighbors search in the Neighbors microservice [ONE-22105](https://support.ataccama.com/jira/browse/ONE-22105)
* Periodicity for Anomaly detection on Time series is set to be 2 for series with no seasonal component, only trend ([ONE-23034](https://support.ataccama.com/jira/browse/ONE-23034))
* Generic API for Anomaly detection. Generic data can be received, no longer restricted by MMM profiles. New processing block of Category.([ONE-19075](https://support.ataccama.com/jira/browse/ONE-19075))
* Term suggestions are fetching changes from DB row-by-row ([ONE-19660](https://support.ataccama.com/jira/browse/ONE-19660))

### Fixed
* Fixed migrations path [ONE-22486](https://support.ataccama.com/jira/browse/ONE-22486)
* Fixed truststore properties [ONE-23118](https://support.ataccama.com/jira/browse/ONE-23118)
* Handling error while refreshing properties/sending heartbeat to Config Service [ONE-23267](https://support.ataccama.com/jira/browse/ONE-23267)
* Fixed bug causing AI Matching to crush in Clustering records phase [ONE-22220](https://support.ataccama.com/jira/browse/ONE-22220)
* Translator sends empty AQL instead of () for unknown query parts [ONE-23404](https://support.ataccama.com/jira/browse/ONE-23404)
* Fix of Anomaly detection bug when using user feedback of confirmed anomalies ([ONE-23092](https://support.ataccama.com/jira/browse/ONE-23092))
* Compile 3rd party dependencies on Centos 7 ([ONE-23555](https://support.ataccama.com/jira/browse/ONE-23555))
* Reduce consumed memory by optimizing imports [ONE-22695](https://support.ataccama.com/jira/browse/ONE-22695)

## 13.1.0 - 2021-05-21
### Added
* HTTP endpoints can use only a subset of enabled authentication methods ([ONE-19663](https://support.ataccama.com/jira/browse/ONE-19663))
* Access to public endpoints can be restricted ([ONE-21896](https://support.ataccama.com/jira/browse/ONE-21896))
* gRPC message limit is configurable ([ONE-21410](https://support.ataccama.com/jira/browse/ONE-21410))
* Absent Configuration Service connection is reported in the logs ([ONE-19900](https://support.ataccama.com/jira/browse/ONE-19900))
* Reason for waiting for a resource is reported in the logs ([ONE-21133](https://support.ataccama.com/jira/browse/ONE-21133))
* Internal encryption of properties ([ONE-19665](https://support.ataccama.com/jira/browse/ONE-19665))
* Module specific metrics were added to AI Matching ([ONE-20995](https://support.ataccama.com/jira/browse/ONE-20995))
* Module specific metrics were added to Anomaly Detection ([ONE-21443](https://support.ataccama.com/jira/browse/ONE-21443))
* Module specific metrics were added to Term Suggestions ([ONE-21375](https://support.ataccama.com/jira/browse/ONE-21375))

### Changed
* Upgrade to Python 3.9 ([ONE-19607](https://support.ataccama.com/jira/browse/ONE-19607))
* Properties reload is applied only when all changed properties can be reloaded ([ONE-19637](https://support.ataccama.com/jira/browse/ONE-19637))
* Keycloak uses same TLS configuration as other HTTP clients ([ONE-21407](https://support.ataccama.com/jira/browse/ONE-21407))
* Configuration for database connection was split into multiple properties ([ONE-19621](https://support.ataccama.com/jira/browse/ONE-19621))
* Waiting for Configuration Service can timeout ([ONE-21631](https://support.ataccama.com/jira/browse/ONE-21631))
* Docker image/zip packages were reduced in size ([ONE-21228](https://support.ataccama.com/jira/browse/ONE-21228))
* Damerau-Levenshtein distance is used in AI Matching suggested rules instead of Affine gap distance ([ONE-21703](https://support.ataccama.com/jira/browse/ONE-21703))
* Dropped support for Oracle DB ([ONE-21741](https://support.ataccama.com/jira/browse/ONE-21741))
* Dropped support for MSSQL DB ([ONE-22155](https://support.ataccama.com/jira/browse/ONE-22155))

### Fixed
* JWT keys can be escaped ([ONE-21383](https://support.ataccama.com/jira/browse/ONE-21383))
* Handling initial empty configuration from Configuration Service ([ONE-21921](https://support.ataccama.com/jira/browse/ONE-21921))
* Fix MSSql issue when getting changes from database ([ONE-21923](https://support.ataccama.com/jira/browse/ONE-21923))
* Only UTC datetime is used ([ONE-21837](https://support.ataccama.com/jira/browse/ONE-21837))
* Required memory (RAM) for Matching Manager was significantly reduced (~80%) ([ONE-21510](https://support.ataccama.com/jira/browse/ONE-21510))

## 13.0.0 - 2021-03-29
...
