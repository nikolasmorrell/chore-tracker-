/**
 * Client-side auth helpers.
 *
 * Phase 2 adds real session handling against the FastAPI /auth endpoints.
 */
export type SessionUser = {
  id: string;
  email: string;
  fullName: string;
  role: "owner" | "admin" | "staff";
  tenantId: string;
};

export async function getSession(): Promise<SessionUser | null> {
  return null;
}
