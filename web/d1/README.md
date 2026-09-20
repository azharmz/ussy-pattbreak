# D1 projection

The projector reads only verified durable R2 pointers for morphology, candidates, T+1 and lifecycle. Every payload is SHA-256 checked before projection.

Projection is serving-only. It cannot mutate Core artifacts.

Run identity is deterministic from the four durable source hashes. Re-running the same source set is idempotent at the D1 row level.

The initial projector deliberately does not infer a Core NEAR_TRIGGER/PRE_BREAKOUT state. Recognized observations without a persisted confirmed breakout are displayed from Core morphology facts and pivot distance.

Extension evidence remains independent and optional.
