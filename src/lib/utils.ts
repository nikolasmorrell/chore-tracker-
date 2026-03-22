export function getWeekOf(date: Date = new Date()): string {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Monday
  d.setDate(diff);
  return d.toISOString().split("T")[0];
}

export function getWeekRange(weekOf: string): { start: string; end: string } {
  const monday = new Date(weekOf + "T00:00:00");
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return {
    start: monday.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    end: sunday.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
  };
}

export function shiftWeek(weekOf: string, direction: number): string {
  const d = new Date(weekOf + "T00:00:00");
  d.setDate(d.getDate() + direction * 7);
  return d.toISOString().split("T")[0];
}
