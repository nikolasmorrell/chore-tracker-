"use client";

import { setPayoutAction } from "@/app/dashboard/actions";

interface Props {
  brotherId: number;
  brotherName: string;
  totalPoints: number;
  currentPayout: number;
  weekOf: string;
}

export default function PayoutCard({ brotherId, brotherName, totalPoints, currentPayout, weekOf }: Props) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-semibold text-lg mb-1">{brotherName}</h3>
      <p className={`text-2xl font-bold mb-3 ${totalPoints >= 0 ? "text-green-600" : "text-red-600"}`}>
        {totalPoints} pts
      </p>
      <form action={setPayoutAction} className="flex items-center gap-2">
        <input type="hidden" name="brotherId" value={brotherId} />
        <input type="hidden" name="weekOf" value={weekOf} />
        <span className="text-gray-500">$</span>
        <input
          name="amount"
          type="number"
          step="0.25"
          min="0"
          defaultValue={currentPayout}
          className="border rounded px-2 py-1 w-24"
        />
        <button
          type="submit"
          className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 transition text-sm"
        >
          Save
        </button>
      </form>
    </div>
  );
}
