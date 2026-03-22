"use client";

import { createChore } from "@/app/chores/actions";
import { useRef } from "react";

export default function AddChoreForm() {
  const formRef = useRef<HTMLFormElement>(null);

  return (
    <form
      ref={formRef}
      action={async (formData) => {
        await createChore(formData);
        formRef.current?.reset();
      }}
      className="flex flex-wrap gap-3 items-end mb-6"
    >
      <div>
        <label className="block text-sm font-medium mb-1">Chore Name</label>
        <input
          name="name"
          type="text"
          required
          placeholder="e.g. Wash dishes"
          className="border rounded px-3 py-2 w-56"
        />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Points</label>
        <input
          name="points"
          type="number"
          required
          placeholder="e.g. 5 or -3"
          className="border rounded px-3 py-2 w-28"
        />
      </div>
      <button
        type="submit"
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
      >
        Add Chore
      </button>
    </form>
  );
}
