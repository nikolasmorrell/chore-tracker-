"use server";

import { revalidatePath } from "next/cache";
import { setPayout, updateBrotherName } from "@/lib/queries";

export async function setPayoutAction(formData: FormData) {
  const brotherId = parseInt(formData.get("brotherId") as string, 10);
  const weekOf = formData.get("weekOf") as string;
  const amount = parseFloat(formData.get("amount") as string);

  if (isNaN(brotherId) || !weekOf || isNaN(amount)) return;

  setPayout(brotherId, weekOf, amount);
  revalidatePath("/dashboard");
}

export async function updateNameAction(formData: FormData) {
  const brotherId = parseInt(formData.get("brotherId") as string, 10);
  const name = formData.get("name") as string;

  if (isNaN(brotherId) || !name || !name.trim()) return;

  updateBrotherName(brotherId, name.trim());
  revalidatePath("/dashboard");
  revalidatePath("/log");
}
