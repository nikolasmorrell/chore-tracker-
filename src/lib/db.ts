import Database from "better-sqlite3";
import path from "path";

const dbPath = path.join(process.cwd(), "data", "chores.db");
const db = new Database(dbPath);

db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

db.exec(`
  CREATE TABLE IF NOT EXISTS brothers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS chores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    points INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS chore_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brother_id INTEGER NOT NULL REFERENCES brothers(id),
    chore_id INTEGER NOT NULL REFERENCES chores(id),
    week_of TEXT NOT NULL,
    logged_at TEXT DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS weekly_payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brother_id INTEGER NOT NULL REFERENCES brothers(id),
    week_of TEXT NOT NULL,
    dollar_amount REAL NOT NULL DEFAULT 0,
    UNIQUE(brother_id, week_of)
  );
`);

// Seed brothers if empty
const count = db.prepare("SELECT COUNT(*) as c FROM brothers").get() as { c: number };
if (count.c === 0) {
  const insert = db.prepare("INSERT INTO brothers (name) VALUES (?)");
  const names = ["Brother 1", "Brother 2", "Brother 3", "Brother 4"];
  for (const name of names) {
    insert.run(name);
  }
}

export default db;
