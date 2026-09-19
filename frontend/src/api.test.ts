import { describe, expect, it } from "vitest";
import { normalizeStatus, pendingFromRecord, traceFromRecord } from "./api";
import type { DecisionRecord, DecisionTrace } from "./types";

const trace: DecisionTrace = {
  trace_version: "1",
  engine_version: "relay-0.1.0",
  ids: { authorization_id: "LA-1", source_authorization_id: "AU0004", request_id: "REQ-1", mandate_id: "TM-1", scenario_id: "SCEN0001" },
  received_at: "2026-09-19T07:00:00Z",
  decided_at: "2026-09-19T07:00:01Z",
  deadline_at: "2026-09-19T07:00:08Z",
  margin_ms: 7000,
  decision: "step_up",
  reason_codes: ["SMALL_OVERSHOOT"],
  customer_message: "This order is slightly above your limit. Approve it?",
  notes: [],
  facts: {
    amounts: { amount: 22, currency: "CHF", billing_amount_chf: 22 },
    merchant: { merchant_id: "ME-1", merchant_name: "Alpine Basket", merchant_category: "groceries", merchant_country: "CH" },
    familiarity: null,
    extracted_item_facts: null,
  },
  guards: [],
  aggregation: { initial: "approve", final: "step_up", raised_by: ["per_order_limit"], uncertainty_policy_applied: false },
  llm: { mode: "off", calls: [] },
  timings: { total_ms: 1.2 },
  resolution: null,
};

const record: DecisionRecord = {
  live_authorization_id: "LA-1",
  run_id: "RUN-1",
  source_authorization_id: "AU0004",
  scenario_id: "SCEN0001",
  replay_order: 4,
  mandate_id: "TM-1",
  sim_timestamp: "2026-08-09T10:00:00Z",
  amount_chf: "22.00",
  currency: "CHF",
  merchant_id: "ME-1",
  merchant_name: "Alpine Basket",
  decision: "step_up",
  status: "pending",
  reason_codes: ["SMALL_OVERSHOOT"],
  customer_message: trace.customer_message,
  notes: [],
  received_at: trace.received_at,
  decided_at: trace.decided_at,
  deadline_at: trace.deadline_at,
  margin_ms: 7000,
  total_ms: 1.2,
  human_deadline_at: "2026-09-19T07:02:00Z",
  trace,
  problems: [],
  resolution: null,
};

describe("Jonas web API adapters", () => {
  it("uses the human deadline for the visible 120 second countdown", () => {
    const pending = pendingFromRecord(record);
    expect(pending.authorization_id).toBe("LA-1");
    expect(pending.expires_at).toBe("2026-09-19T07:02:00Z");
    expect(pending.trace.customer_message).toMatch(/Approve/);
  });

  it("keeps the full trace and can safely display an invalid event without one", () => {
    expect(traceFromRecord(record).guards).toEqual([]);
    const invalid = traceFromRecord({ ...record, trace: null, reason_codes: ["INVALID_EVENT"], merchant_name: null, amount_chf: null });
    expect(invalid.ids.authorization_id).toBe("LA-1");
    expect(invalid.facts.merchant.merchant_name).toBe("Unknown merchant");
    expect(invalid.reason_codes).toEqual(["INVALID_EVENT"]);
  });

  it("reads scenarios and the deadline margin from the nested status response", () => {
    const status = normalizeStatus({
      engine_mode: "deterministic",
      llm_mode: "off",
      bootstrap: { scenarios: [{ scenario_id: "SCEN0001", name: "Groceries", event_count: 10 }] },
      bootstrap_error: null,
      worker: { state: "polling", last_margin_ms: 7123, active_run_ids: ["RUN-1"] },
    });
    expect(status.connected).toBe(true);
    expect(status.latest_margin_ms).toBe(7123);
    expect(status.scenarios).toEqual([{ scenario_id: "SCEN0001", name: "Groceries", purchase_count: 10 }]);
  });
});
