export const SCHEMA = [
  "CREATE TABLE IF NOT EXISTS dashboard_opportunities(id TEXT PRIMARY KEY NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)))",
  "CREATE TABLE IF NOT EXISTS dashboard_positions(id TEXT PRIMARY KEY NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)))",
  "CREATE TABLE IF NOT EXISTS dashboard_current(singleton INTEGER PRIMARY KEY CHECK(singleton=1),payload TEXT NOT NULL CHECK(json_valid(payload)))",
  "CREATE TABLE IF NOT EXISTS dashboard_validation(singleton INTEGER PRIMARY KEY CHECK(singleton=1),valid INTEGER NOT NULL CHECK(valid=1))",
];
