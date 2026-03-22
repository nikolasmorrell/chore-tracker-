"use server";

import { revalidatePath } from "next/cache";
import { logChore, removeLog } from "@/lib/queries";
import { getWeekOf } from "@/lib/utils";

export async function logChoreAction(formData: FormData) {
  const brotherId = parseInt(formData.get("brotherId") as string, 10);
  const choreId = parseInt(formData.get("choreId") as string, 10);

  if (isNaN(brotherId) || isNaN(choreId)) return;

  const weekOf = getWeekOf();
  logChore(brotherId, choreId, weekOf);
  revalidatePath("/log");
}

export async function removeLogAction(formData: FormData) {
  const logId = parseInt(formData.get("logId") as string, 10);
  if (isNaN(logId)) return;

  removeLog(logId);
  revalidatePath("/log");
}
