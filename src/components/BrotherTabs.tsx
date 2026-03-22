"use client";

import { useRouter, useSearchParams } from "next/navigation";

interface Brother {
  id: number;
  name: string;
}

export default function BrotherTabs({ brothers, activeBrotherId }: { brothers: Brother[]; activeBrotherId: number }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  function switchBrother(id: number) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("brother", id.toString());
    router.push(`/log?${params.toString()}`);
  }

  return (
    <div className="flex gap-2 mb-6">
      {brothers.map((b) => (
        <button
          key={b.id}
          onClick={() => switchBrother(b.id)}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            b.id === activeBrotherId
              ? "bg-blue-600 text-white"
              : "bg-white text-gray-700 hover:bg-gray-100 shadow"
          }`}
        >
          {b.name}
        </button>
      ))}
    </div>
  );
}
