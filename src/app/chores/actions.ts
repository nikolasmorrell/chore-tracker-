"use server";

import { revalidatePath } from "next/cache";
import { addChore, removeChore } from "@/lib/queries";

export async function createChore(formData: FormData) {
  const name = formData.get("name") as string;
  const points = parseInt(formData.get("points") as string, 10);

  if (!name || !name.trim()) return;
  if (isNaN(points)) return;

  addChore(name.trim(), points);
  revalidatePath("/chores");
}

export async function deleteChore(formData: FormData) {
  const id = parseInt(formData.get("id") as string, 10);
  if (isNaN(id)) return;

  removeChore(id);
  revalidatePath("/chores");
}
