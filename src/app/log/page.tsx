import { getBrothers, getAllChores, getWeeklyLogsByBrother } from "@/lib/queries";
import { getWeekOf, getWeekRange } from "@/lib/utils";
import { logChoreAction, removeLogAction } from "./actions";
import BrotherTabs from "@/components/BrotherTabs";

export const dynamic = "force-dynamic";

export default function LogPage({
  searchParams,
}: {
  searchParams: { brother?: string };
}) {
  const brothers = getBrothers();
  const chores = getAllChores();
  const weekOf = getWeekOf();
  const range = getWeekRange(weekOf);

  const activeBrotherId = searchParams.brother
    ? parseInt(searchParams.brother, 10)
    : brothers[0]?.id ?? 1;

  const logs = getWeeklyLogsByBrother(activeBrotherId, weekOf);
  const totalPoints = logs.reduce((sum, l) => sum + l.points, 0);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Weekly Chore Log</h1>
      <p className="text-gray-500 mb-4">
        Week of {range.start} &ndash; {range.end}
      </p>

      <BrotherTabs brothers={brothers} activeBrotherId={activeBrotherId} />

      {chores.length === 0 ? (
        <p className="text-gray-500">
          No chores available. Go to the Chores page to add some first.
        </p>
      ) : (
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h2 className="font-semibold mb-3">Log a Chore</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {chores.map((chore) => (
              <form key={chore.id} action={logChoreAction}>
                <input type="hidden" name="brotherId" value={activeBrotherId} />
                <input type="hidden" name="choreId" value={chore.id} />
                <button
                  type="submit"
                  className="w-full text-left px-3 py-2 border rounded hover:bg-blue-50 transition flex justify-between items-center"
                >
                  <span>{chore.name}</span>
                  <span
                    className={`text-sm font-semibold ${
                      chore.points >= 0 ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {chore.points > 0 ? "+" : ""}
                    {chore.points}
                  </span>
                </button>
              </form>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-3">
          <h2 className="font-semibold">Logged This Week</h2>
          <span
            className={`text-lg font-bold ${
              totalPoints >= 0 ? "text-green-600" : "text-red-600"
            }`}
          >
            {totalPoints} pts
          </span>
        </div>

        {logs.length === 0 ? (
          <p className="text-gray-400">Nothing logged yet this week.</p>
        ) : (
          <ul className="divide-y">
            {logs.map((log) => (
              <li key={log.id} className="flex justify-between items-center py-2">
                <div>
                  <span className="font-medium">{log.chore_name}</span>
                  <span
                    className={`ml-2 text-sm ${
                      log.points >= 0 ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {log.points > 0 ? "+" : ""}
                    {log.points}
                  </span>
                </div>
                <form action={removeLogAction}>
                  <input type="hidden" name="logId" value={log.id} />
                  <button
                    type="submit"
                    className="text-red-400 hover:text-red-600 text-sm"
                  >
                    Remove
                  </button>
                </form>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
