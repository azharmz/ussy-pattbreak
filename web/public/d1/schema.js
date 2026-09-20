export const SCHEMA = [
  "CREATE TABLE IF NOT EXISTS dashboard_opportunities(id TEXT PRIMARY KEY NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)))",
  "CREATE TABLE IF NOT EXISTS dashboard_positions(id TEXT PRIMARY KEY NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)))",
  "CREATE TABLE IF NOT EXISTS dashboard_current(singleton INTEGER PRIMARY KEY CHECK(singleton=1),payload TEXT NOT NULL CHECK(json_valid(payload)))",
  "CREATE TABLE IF NOT EXISTS dashboard_validation(singleton INTEGER PRIMARY KEY CHECK(singleton=1),valid INTEGER NOT NULL CHECK(valid=1))",
  "CREATE TABLE IF NOT EXISTS dashboard_opportunities_v8(generation TEXT NOT NULL,id TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),PRIMARY KEY(generation,id))",
  "CREATE TABLE IF NOT EXISTS dashboard_positions_v8(generation TEXT NOT NULL,id TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),PRIMARY KEY(generation,id))",
  "CREATE TABLE IF NOT EXISTS dashboard_sync_v8(singleton INTEGER PRIMARY KEY CHECK(singleton=1),payload TEXT NOT NULL CHECK(json_valid(payload)))",
];
