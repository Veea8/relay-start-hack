export type Decision = "approve" | "decline" | "step_up";
export type GuardVerdict = "PASS" | "STEP_UP" | "DECLINE" | "UNCERTAIN" | "SKIP";
export type GuardFamily =
  | "Spending limits"
  | "Item and terms"
  | "Seller"
  | "Session"
  | "Repeats and manipulation";

export interface EvidenceItem {
  fact: string;
  value: string | number | boolean | null;
  comparator: string | null;
  threshold: string | number | boolean | null;
  source: string;
}

export interface GuardResult {
  guard_number: number;
  guard_id: string;
  family: GuardFamily;
  verdict: GuardVerdict;
  reason_code: string | null;
  evidence: EvidenceItem[];
  signal: { name: string; strength: "normal" | "strong" } | null;
  note: string | null;
  customer_message: string | null;
  elapsed_ms: number;
}

export interface DecisionTrace {
  trace_version: string;
  engine_version: string;
  ids: {
    authorization_id: string;
    source_authorization_id: string;
    request_id: string;
    mandate_id: string;
    scenario_id: string;
  };
  received_at: string;
  decided_at: string;
  deadline_at: string;
  margin_ms: number;
  decision: Decision;
  reason_codes: string[];
  customer_message: string;
  notes: string[];
  facts: {
    amounts: { amount: number; currency: string; billing_amount_chf: number };
    merchant: {
      merchant_id: string;
      merchant_name: string;
      merchant_category: string;
      merchant_country: string;
    };
    familiarity: Record<string, unknown> | null;
    extracted_item_facts: Record<string, unknown> | null;
  };
  guards: GuardResult[];
  aggregation: {
    initial: Decision;
    final: Decision;
    raised_by: string[];
    uncertainty_policy_applied: boolean;
  };
  llm: { mode: string; calls: Record<string, unknown>[] };
  timings: { total_ms: number };
  resolution: Record<string, unknown> | null;
}

export interface PendingAuthorization {
  authorization_id: string;
  created_at: string;
  expires_at: string;
  trace: DecisionTrace;
}

export interface HardRule {
  field: string;
  operator: string;
  value: string | number | boolean;
  currency?: string;
  scope?: string;
}

export interface PolicyDraft {
  draft_id?: string;
  mandate_id?: string;
  status: "compiled" | "draft" | "active" | "revoked";
  instruction: string;
  hard_rules: HardRule[];
  uncertainty_policy: "ask" | "decline" | "approve";
  guidance: string[];
  open_questions: string[];
  checks: PolicyCheck[];
}

export interface PolicyCheck {
  label: string;
  detail: string;
  stored_with_platform: boolean;
}

export interface Scenario {
  scenario_id: string;
  name: string;
  purchase_count: number;
}

export interface EngineStatus {
  connected: boolean;
  environment: "mock" | "offline" | "live";
  engine_mode: "deterministic" | "model" | "degraded";
  model_name: string | null;
  latest_margin_ms: number | null;
  active_run_id: string | null;
  scenarios: Scenario[];
}

export type StreamEvent =
  | { type: "decision"; data: DecisionTrace }
  | { type: "pending"; data: PendingAuthorization }
  | { type: "resolution"; data: DecisionTrace }
  | { type: "status"; data: EngineStatus };

export interface DecisionRecord {
  live_authorization_id: string;
  run_id: string;
  source_authorization_id: string | null;
  scenario_id: string | null;
  replay_order: number | null;
  mandate_id: string | null;
  sim_timestamp: string | null;
  amount_chf: string | null;
  currency: string | null;
  merchant_id: string | null;
  merchant_name: string | null;
  decision: Decision;
  status: "approved" | "declined" | "pending" | "expired" | "cancelled";
  reason_codes: string[];
  customer_message: string;
  notes: string[];
  received_at: string;
  decided_at: string;
  deadline_at: string;
  margin_ms: number;
  total_ms: number;
  human_deadline_at: string | null;
  trace: DecisionTrace | null;
  problems: string[];
  resolution: Record<string, unknown> | null;
}
