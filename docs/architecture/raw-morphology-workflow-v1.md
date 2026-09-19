# RAW_ONEIL_MORPHOLOGY workflow

This is the heavy-stage recovery boundary after FROZEN_READY.

The workflow checks out the O'Neil engine at the exact frozen commit
`c433cc1e35a5aa32a46f732cd8c5545935e36e40`, freezes the current canonical
READY v2 object, verifies its immutable Parquet SHA-256, and runs morphology.

Artifacts:

- `frozen-ready.json`
- `raw-oneil-morphology.json` — lineage/checkpoint metadata
- `raw-oneil-morphology.jsonl` — deterministic frozen engine records

Downstream breakout/entry/lifecycle work should consume these artifacts rather
than rerun morphology when the checkpoint lineage is still valid.

The R2 credentials used here must be read-only. The workflow performs no R2
write/delete operation. It remains manual-dispatch until an auditable production
trigger is deliberately approved.
