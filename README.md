# tpp-database-utils

These are some utilities for interacting with an OpenSAFELY TPP database. It contains:

* a check for "database maintenance mode"
* an importer for a custom medication dictionary that is used to work around some observed data quality errors.

This is packaged as a docker container and run inside the secure environment by the [job-runner](https://github.com/opensafely-core/job-runner).

## Developer docs

Please see the [additional information](DEVELOPERS.md).
