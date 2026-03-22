import { getAllChores } from "@/lib/queries";
import { deleteChore } from "./actions";
import AddChoreForm from "@/components/AddChoreForm";

export const dynamic = "force-dynamic";

export default function ChoresPage() {
  const chores = getAllChores();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Manage Chores</h1>
      <AddChoreForm />

      {chores.length === 0 ? (
        <p className="text-gray-500">No chores yet. Add one above!</p>
      ) : (
        <table className="w-full bg-white rounded-lg shadow overflow-hidden">
          <thead className="bg-gray-100">
            <tr>
              <th className="text-left px-4 py-3">Chore</th>
              <th className="text-right px-4 py-3">Points</th>
              <th className="text-right px-4 py-3 w-24">Action</th>
            </tr>
          </thead>
          <tbody>
            {chores.map((chore) => (
              <tr key={chore.id} className="border-t">
                <td className="px-4 py-3">{chore.name}</td>
                <td
                  className={`px-4 py-3 text-right font-semibold ${
                    chore.points >= 0 ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {chore.points > 0 ? "+" : ""}
                  {chore.points}
                </td>
                <td className="px-4 py-3 text-right">
                  <form action={deleteChore}>
                    <input type="hidden" name="id" value={chore.id} />
                    <button
                      type="submit"
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      Delete
                    </button>
                  </form>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
