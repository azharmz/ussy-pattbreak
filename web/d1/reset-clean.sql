-- D1 is disposable serving state. Immutable history remains in R2.
-- Destructive by design: run only through the manual clean-rebuild workflow.
DROP TABLE IF EXISTS dashboard_validation;
DROP TABLE IF EXISTS dashboard_current;
DROP TABLE IF EXISTS dashboard_opportunities_v8;
DROP TABLE IF EXISTS dashboard_positions_v8;
DROP TABLE IF EXISTS projection_runs;
DROP TABLE IF EXISTS opportunity_evidence;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS opportunities;
DROP TABLE IF EXISTS positions;
DROP TABLE IF EXISTS projection_state;
DROP TABLE IF EXISTS current_opportunities;
DROP TABLE IF EXISTS current_breakout_events;
DROP TABLE IF EXISTS current_positions;

CREATE TABLE projection_state(
  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
  payload TEXT NOT NULL CHECK(json_valid(payload))
);
CREATE TABLE current_opportunities(
  generation TEXT NOT NULL,
  event_id TEXT NOT NULL,
  payload TEXT NOT NULL CHECK(json_valid(payload)),
  PRIMARY KEY(generation,event_id)
);
CREATE TABLE current_breakout_events(
  generation TEXT NOT NULL,
  event_id TEXT NOT NULL,
  payload TEXT NOT NULL CHECK(json_valid(payload)),
  PRIMARY KEY(generation,event_id)
);
CREATE TABLE current_positions(
  generation TEXT NOT NULL,
  position_id TEXT NOT NULL,
  payload TEXT NOT NULL CHECK(json_valid(payload)),
  PRIMARY KEY(generation,position_id)
);
