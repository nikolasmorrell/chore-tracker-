import { getWeeklySummary, getWeeklyLogs, getPayouts } from "@/lib/queries";
import { getWeekOf, getWeekRange } from "@/lib/utils";
import WeekNavigator from "@/components/WeekNavigator";
import PayoutCard from "@/components/PayoutCard";

export const dynamic = "force-dynamic";

export default function DashboardPage({
  searchParams,
}: {
  searchParams: { week?: string };
}) {
  const weekOf = searchParams.week || getWeekOf();
  const range = getWeekRange(weekOf);
  const summary = getWeeklySummary(weekOf);
  const logs = getWeeklyLogs(weekOf);
  const payouts = getPayouts(weekOf);

  const payoutMap = new Map(payouts.map((p) => [p.brother_id, p.dollar_amount]));

  // Group logs by brother
  const logsByBrother = new Map<number, typeof logs>();
  for (const log of logs) {
    if (!logsByBrother.has(log.brother_id)) logsByBrother.set(log.brother_id, []);
    logsByBrother.get(log.brother_id)!.push(log);
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Dad&apos;s Dashboard</h1>
      <WeekNavigator weekOf={weekOf} range={range} />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {summary.map((s) => (
          <PayoutCard
            key={s.brother_id}
            brotherId={s.brother_id}
            brotherName={s.brother_name}
            totalPoints={s.total_points}
            currentPayout={payoutMap.get(s.brother_id) ?? 0}
            weekOf={weekOf}
          />
        ))}
      </div>

      <h2 className="text-xl font-semibold mb-4">Detailed Log</h2>
      {summary.map((s) => {
        const brotherLogs = logsByBrother.get(s.brother_id) ?? [];
        return (
          <div key={s.brother_id} className="mb-6">
            <h3 className="font-semibold text-lg mb-2">{s.brother_name}</h3>
            {brotherLogs.length === 0 ? (
              <p className="text-gray-400 ml-4">No chores logged this week.</p>
            ) : (
              <table className="w-full bg-white rounded shadow overflow-hidden mb-2">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left px-4 py-2 text-sm">Chore</th>
                    <th className="text-right px-4 py-2 text-sm">Points</th>
                    <th className="text-right px-4 py-2 text-sm">When</th>
                  </tr>
                </thead>
                <tbody>
                  {brotherLogs.map((log) => (
                    <tr key={log.id} className="border-t">
                      <td className="px-4 py-2">{log.chore_name}</td>
                      <td
                        className={`px-4 py-2 text-right font-semibold ${
                          log.points >= 0 ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {log.points > 0 ? "+" : ""}
                        {log.points}
                      </td>
                      <td className="px-4 py-2 text-right text-gray-400 text-sm">
                        {new Date(log.logged_at + "Z").toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        );
      })}
    </div>
  );
}
