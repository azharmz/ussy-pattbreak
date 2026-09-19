# FROZEN_READY Runtime v1

This is the first executable real-data boundary.

The runtime uses only S3-compatible `get_object` calls:

1. read `production/ready/current.json`;
2. validate READY v2 and freeze its immutable object identity;
3. read the exact immutable Parquet object;
4. compute SHA-256 locally and compare with the manifest;
5. re-read `current.json` and fail if the pointer changed during the operation;
6. emit a JSON FROZEN_READY checkpoint.

The GitHub workflow uploads only checkpoint metadata as a durable artifact. It
does not upload the READY Parquet and does not perform morphology compute.

Repository secrets must contain a read-only R2 credential for the `ussy-data`
bucket. The code itself never calls `put_object`, delete, or producer APIs.

A successful FROZEN_READY artifact is necessary but not sufficient for the next
stage. RAW_ONEIL_MORPHOLOGY must consume the exact immutable Parquet key/hash
recorded here and retain this lineage.
