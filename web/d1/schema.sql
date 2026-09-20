PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projection_runs (
  run_id TEXT PRIMARY KEY,
  as_of_date TEXT NOT NULL,
  ready_source_hash TEXT,
  morphology_source_hash TEXT,
  candidate_source_hash TEXT,
  t1_source_hash TEXT,
  lifecycle_source_hash TEXT,
  engine_version TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  producer_commit TEXT,
  created_at TEXT NOT NULL,
  projected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opportunities (
  assessment_id TEXT PRIMARY KEY,
  base_id TEXT NOT NULL,
  lineage_id TEXT NOT NULL,
  security_id TEXT NOT NULL,
  ticker TEXT NOT NULL,
  pattern_type TEXT NOT NULL,
  morphology_status TEXT NOT NULL,
  native_state TEXT,
  candidate_semantics TEXT,
  structural_start TEXT,
  structural_end TEXT,
  pivot_source_date TEXT,
  pivot_level REAL,
  depth_pct REAL,
  as_of_date TEXT NOT NULL,
  as_of_close REAL,
  distance_to_pivot_pct REAL,
  breakout_state TEXT,
  breakout_close REAL,
  volume_ratio REAL,
  signal_date TEXT,
  t1_open REAL,
  open_extension_pct REAL,
  t1_status TEXT,
  entry_date TEXT,
  entry_price REAL,
  source_hash TEXT NOT NULL,
  projection_run_id TEXT NOT NULL,
  FOREIGN KEY (projection_run_id) REFERENCES projection_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_opportunities_asof ON opportunities(as_of_date DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_ticker ON opportunities(ticker, as_of_date DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_base ON opportunities(base_id, as_of_date DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_lineage ON opportunities(lineage_id, as_of_date DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_breakout ON opportunities(breakout_state, as_of_date DESC);

CREATE TABLE IF NOT EXISTS positions (
  position_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL,
  assessment_id TEXT,
  base_id TEXT,
  lineage_id TEXT,
  security_id TEXT NOT NULL,
  ticker TEXT,
  pattern_type TEXT,
  pivot_level REAL,
  breakout_date TEXT,
  entry_date TEXT,
  entry_price REAL,
  state TEXT NOT NULL,
  current_price REAL,
  unrealized_return_pct REAL,
  exit_signal_date TEXT,
  exit_reason TEXT,
  exit_date TEXT,
  exit_price REAL,
  eight_week_state TEXT,
  eight_week_first_rapid_winner_date TEXT,
  last_evaluated_date TEXT,
  as_of_date TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  projection_run_id TEXT NOT NULL,
  FOREIGN KEY (projection_run_id) REFERENCES projection_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_positions_state ON positions(state, as_of_date DESC);
CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker, as_of_date DESC);

CREATE TABLE IF NOT EXISTS opportunity_evidence (
  evidence_id TEXT PRIMARY KEY,
  assessment_id TEXT NOT NULL,
  base_id TEXT NOT NULL,
  lineage_id TEXT NOT NULL,
  opportunity_id TEXT NOT NULL,
  extension_type TEXT NOT NULL,
  extension_version TEXT NOT NULL,
  as_of_date TEXT NOT NULL,
  evidence_state TEXT NOT NULL CHECK (evidence_state IN ('NOT_AVAILABLE','NOT_EVALUABLE','NOT_CONFIRMED','CONFIRMED')),
  evidence_payload TEXT,
  source_identity TEXT,
  source_hash TEXT,
  created_at TEXT,
  projection_run_id TEXT NOT NULL,
  FOREIGN KEY (assessment_id) REFERENCES opportunities(assessment_id),
  FOREIGN KEY (projection_run_id) REFERENCES projection_runs(run_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_observation_engine
ON opportunity_evidence(assessment_id, extension_type, extension_version, as_of_date);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  position_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_date TEXT NOT NULL,
  event_price REAL,
  reason TEXT,
  source_hash TEXT NOT NULL,
  projection_run_id TEXT NOT NULL,
  FOREIGN KEY (position_id) REFERENCES positions(position_id),
  FOREIGN KEY (projection_run_id) REFERENCES projection_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_events_position ON events(position_id, event_date);
