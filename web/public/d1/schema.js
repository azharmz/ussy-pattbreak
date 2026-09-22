export const SCHEMA = [
  "CREATE TABLE IF NOT EXISTS projection_state(singleton INTEGER PRIMARY KEY CHECK(singleton=1),payload TEXT NOT NULL CHECK(json_valid(payload)))",
  "CREATE TABLE IF NOT EXISTS current_opportunities(generation TEXT NOT NULL,event_id TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),PRIMARY KEY(generation,event_id))",
  "CREATE TABLE IF NOT EXISTS current_breakout_events(generation TEXT NOT NULL,event_id TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),PRIMARY KEY(generation,event_id))",
  "CREATE TABLE IF NOT EXISTS current_positions(generation TEXT NOT NULL,position_id TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),PRIMARY KEY(generation,position_id))",
  "CREATE TABLE IF NOT EXISTS historical_breakout_events(signal_date TEXT NOT NULL,event_id TEXT NOT NULL,generation TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),PRIMARY KEY(signal_date,event_id))",
  "CREATE TABLE IF NOT EXISTS historical_positions(as_of_date TEXT NOT NULL,position_id TEXT NOT NULL,generation TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),PRIMARY KEY(as_of_date,position_id))"
];
