/**
 * Session helpers (thin wrappers over /auth endpoints).
 *
 * Real session state is tracked by httpOnly cookies set by the backend.
 */
import { api } from "./api";

export type Role = "owner" | "admin" | "staff";

export type SessionUser = {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  tenant_id: string;
};

export async function logout(): Promise<void> {
  try {
    await api.post("/api/v1/auth/logout");
  } catch {
    /* best-effort */
  }
}
