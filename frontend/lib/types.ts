/**
 * API response & DTO types mirroring the backend pydantic schemas.
 */

export type Role = "owner" | "admin" | "staff";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan: "trial" | "starter" | "pro" | "enterprise";
  status: string;
  trial_ends_at: string | null;
  twilio_phone_number: string | null;
  created_at: string;
}

export interface Customer {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  address: Record<string, unknown> | null;
  notes: string | null;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  customer_id: string | null;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  status: "pending" | "ocr" | "extracting" | "ready" | "failed";
  doc_type: "insurance_cert" | "permit" | "contract" | "lien_waiver" | "other";
  created_at: string;
}

export interface DocumentExtraction {
  id: string;
  document_id: string;
  claude_model: string;
  prompt_version: string;
  structured: Record<string, unknown>;
  confidence: number | null;
  created_at: string;
}

export interface Alert {
  id: string;
  document_id: string;
  kind:
    | "expiring_30"
    | "expiring_14"
    | "expiring_7"
    | "expiring_0"
    | "missing_field";
  due_at: string;
  status: "scheduled" | "sent" | "dismissed";
  channel: "email" | "sms" | "inapp";
  sent_at: string | null;
  created_at: string;
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  source: "document" | "call" | "manual" | "alert";
  source_id: string | null;
  assigned_to: string | null;
  due_at: string | null;
  priority: "low" | "normal" | "high" | "urgent";
  status: "open" | "in_progress" | "done" | "cancelled";
  created_at: string;
}

export interface Call {
  id: string;
  twilio_call_sid: string;
  from_number: string;
  to_number: string;
  direction: "inbound" | "outbound";
  status: string;
  started_at: string | null;
  ended_at: string | null;
  summary: string | null;
  intent: string | null;
  transferred_to: string | null;
}

export interface CallTurn {
  id: string;
  turn_index: number;
  speaker: "caller" | "assistant";
  text: string;
  latency_ms: number | null;
  created_at: string;
}

export interface CallDetail extends Call {
  turns: CallTurn[];
}

export interface CursorPage<T> {
  items: T[];
  next_cursor: string | null;
}

export interface DocumentUploadResponse {
  document_id: string;
  upload_url: string;
  fields: Record<string, string>;
}
