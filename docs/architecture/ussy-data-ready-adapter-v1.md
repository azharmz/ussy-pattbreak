# ussy-data READY Adapter v1

The consumer contract is based on the canonical private R2 pointer
`production/ready/current.json`.

The upstream `ussy-data` contract currently publishes READY schema v2 with an
immutable date-keyed Parquet object under `production/ready/runs/`, its SHA-256,
security identities, and as-of/terminal-date metadata.

Pattern Breakout freezes:

```
ussy-data:production/ready/current.json
  -> exact production/ready/runs/<as_of_date>.parquet
  -> exact sha256
  -> FROZEN_READY
```

The adapter rejects schema v1, mutable/non-run object paths, malformed hashes,
as-of/terminal-date disagreement, duplicate/inconsistent security identities,
and timezone-naive publication timestamps.

This module does not fetch credentials and does not copy `ussy-data` producer
logic. A thin runtime wrapper may read the private pointer using a read-only R2
credential, then pass the manifest to this adapter. The upstream Parquet body
must still be checksum-verified against the frozen SHA before morphology compute.

The READY dataset is rolling (upstream currently targets at most 300 bars and a
minimum-ready threshold of 250). READY means upstream history eligibility; it is
not by itself a Pattern Breakout morphology or signal verdict.
