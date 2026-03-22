"use client";

import { useRouter } from "next/navigation";
import { shiftWeek } from "@/lib/utils";

export default function WeekNavigator({ weekOf, range }: { weekOf: string; range: { start: string; end: string } }) {
  const router = useRouter();

  function navigate(direction: number) {
    const newWeek = shiftWeek(weekOf, direction);
    router.push(`/dashboard?week=${newWeek}`);
  }

  return (
    <div className="flex items-center gap-4 mb-6">
      <button
        onClick={() => navigate(-1)}
        className="px-3 py-1 bg-white rounded shadow hover:bg-gray-100 transition"
      >
        &larr; Prev
      </button>
      <span className="text-lg font-medium">
        {range.start} &ndash; {range.end}
      </span>
      <button
        onClick={() => navigate(1)}
        className="px-3 py-1 bg-white rounded shadow hover:bg-gray-100 transition"
      >
        Next &rarr;
      </button>
    </div>
  );
}
