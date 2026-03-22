import db from "./db";

export interface Chore {
  id: number;
  name: string;
  points: number;
  created_at: string;
}

export interface Brother {
  id: number;
  name: string;
}

export interface ChoreLog {
  id: number;
  brother_id: number;
  chore_id: number;
  week_of: string;
  logged_at: string;
  chore_name: string;
  points: number;
  brother_name: string;
}

export interface WeeklySummary {
  brother_id: number;
  brother_name: string;
  total_points: number;
}

export interface Payout {
  brother_id: number;
  brother_name: string;
  dollar_amount: number;
}

// Chores
export function getAllChores(): Chore[] {
  return db.prepare("SELECT * FROM chores ORDER BY points DESC").all() as Chore[];
}

export function addChore(name: string, points: number): void {
  db.prepare("INSERT INTO chores (name, points) VALUES (?, ?)").run(name, points);
}

export function removeChore(id: number): void {
  db.prepare("DELETE FROM chore_logs WHERE chore_id = ?").run(id);
  db.prepare("DELETE FROM chores WHERE id = ?").run(id);
}

// Brothers
export function getBrothers(): Brother[] {
  return db.prepare("SELECT * FROM brothers ORDER BY id").all() as Brother[];
}

export function updateBrotherName(id: number, name: string): void {
  db.prepare("UPDATE brothers SET name = ? WHERE id = ?").run(name, id);
}

// Chore Logs
export function logChore(brotherId: number, choreId: number, weekOf: string): void {
  db.prepare(
    "INSERT INTO chore_logs (brother_id, chore_id, week_of) VALUES (?, ?, ?)"
  ).run(brotherId, choreId, weekOf);
}

export function removeLog(logId: number): void {
  db.prepare("DELETE FROM chore_logs WHERE id = ?").run(logId);
}

export function getWeeklyLogsByBrother(brotherId: number, weekOf: string): ChoreLog[] {
  return db
    .prepare(
      `SELECT cl.id, cl.brother_id, cl.chore_id, cl.week_of, cl.logged_at,
              c.name as chore_name, c.points, b.name as brother_name
       FROM chore_logs cl
       JOIN chores c ON cl.chore_id = c.id
       JOIN brothers b ON cl.brother_id = b.id
       WHERE cl.brother_id = ? AND cl.week_of = ?
       ORDER BY cl.logged_at DESC`
    )
    .all(brotherId, weekOf) as ChoreLog[];
}

export function getWeeklyLogs(weekOf: string): ChoreLog[] {
  return db
    .prepare(
      `SELECT cl.id, cl.brother_id, cl.chore_id, cl.week_of, cl.logged_at,
              c.name as chore_name, c.points, b.name as brother_name
       FROM chore_logs cl
       JOIN chores c ON cl.chore_id = c.id
       JOIN brothers b ON cl.brother_id = b.id
       WHERE cl.week_of = ?
       ORDER BY b.name, cl.logged_at DESC`
    )
    .all(weekOf) as ChoreLog[];
}

export function getWeeklySummary(weekOf: string): WeeklySummary[] {
  return db
    .prepare(
      `SELECT b.id as brother_id, b.name as brother_name,
              COALESCE(SUM(c.points), 0) as total_points
       FROM brothers b
       LEFT JOIN chore_logs cl ON b.id = cl.brother_id AND cl.week_of = ?
       LEFT JOIN chores c ON cl.chore_id = c.id
       GROUP BY b.id
       ORDER BY b.id`
    )
    .all(weekOf) as WeeklySummary[];
}

// Payouts
export function setPayout(brotherId: number, weekOf: string, amount: number): void {
  db.prepare(
    `INSERT INTO weekly_payouts (brother_id, week_of, dollar_amount)
     VALUES (?, ?, ?)
     ON CONFLICT(brother_id, week_of)
     DO UPDATE SET dollar_amount = excluded.dollar_amount`
  ).run(brotherId, weekOf, amount);
}

export function getPayouts(weekOf: string): Payout[] {
  return db
    .prepare(
      `SELECT b.id as brother_id, b.name as brother_name,
              COALESCE(wp.dollar_amount, 0) as dollar_amount
       FROM brothers b
       LEFT JOIN weekly_payouts wp ON b.id = wp.brother_id AND wp.week_of = ?
       ORDER BY b.id`
    )
    .all(weekOf) as Payout[];
}
