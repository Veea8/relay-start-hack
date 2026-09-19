import type {
  Decision,
  DecisionTrace,
  EngineStatus,
  GuardFamily,
  GuardResult,
  GuardVerdict,
  PendingAuthorization,
  PolicyDraft,
} from "./types";

const families: GuardFamily[] = [
  "Spending limits",
  "Item and terms",
  "Seller",
  "Session",
  "Repeats and manipulation",
];

const representativeGuards = (
  decisiveFamily: GuardFamily,
  verdict: GuardVerdict,
  reason: string | null,
  amount: number,
  threshold: number,
): GuardResult[] =>
  families.flatMap((family, familyIndex) => {
    const count = family === "Spending limits" ? 3 : 2;
    return Array.from({ length: count }, (_, index) => {
      const isDecisive = family === decisiveFamily && index === 0;
      return {
        guard_number: familyIndex * 4 + index + 1,
        guard_id: isDecisive
          ? reason?.toLowerCase() ?? "policy_check"
          : `${family.toLowerCase().replaceAll(" ", "_")}_${index + 1}`,
        family,
        verdict: isDecisive ? verdict : index === 0 ? "PASS" : "SKIP",
        reason_code: isDecisive ? reason : null,
        evidence: isDecisive
          ? [
              {
                fact: "billing_amount_chf",
                value: amount,
                comparator: amount > threshold ? ">" : "<=",
                threshold,
                source: "authorization against confirmed policy",
              },
            ]
          : [],
        signal: null,
        note: null,
        customer_message: null,
        elapsed_ms: Number((0.05 + familyIndex * 0.017 + index * 0.009).toFixed(3)),
      };
    });
  });

function trace(
  authorizationId: string,
  sourceId: string,
  merchant: string,
  category: string,
  amount: number,
  decision: Decision,
  message: string,
  family: GuardFamily,
  guardVerdict: GuardVerdict,
  reason: string | null,
  threshold: number,
  minuteOffset: number,
): DecisionTrace {
  const decidedAt = new Date(Date.now() - minuteOffset * 60_000);
  return {
    trace_version: "1",
    engine_version: "relay-0.1.0",
    ids: {
      authorization_id: authorizationId,
      source_authorization_id: sourceId,
      request_id: `req_${authorizationId.toLowerCase()}`,
      mandate_id: "TM-DEMO-0001",
      scenario_id: "SCEN0001",
    },
    received_at: new Date(decidedAt.getTime() - 34).toISOString(),
    decided_at: decidedAt.toISOString(),
    deadline_at: new Date(decidedAt.getTime() + 7_824).toISOString(),
    margin_ms: 7824,
    decision,
    reason_codes: reason ? [reason] : [],
    customer_message: message,
    notes: [],
    facts: {
      amounts: { amount, currency: "CHF", billing_amount_chf: amount },
      merchant: {
        merchant_id: `ME-${authorizationId.slice(-4)}`,
        merchant_name: merchant,
        merchant_category: category,
        merchant_country: "CH",
      },
      familiarity: null,
      extracted_item_facts: null,
    },
    guards: representativeGuards(family, guardVerdict, reason, amount, threshold),
    aggregation: {
      initial: "approve",
      final: decision,
      raised_by: reason ? [reason.toLowerCase()] : [],
      uncertainty_policy_applied: guardVerdict === "UNCERTAIN",
    },
    llm: { mode: "off", calls: [] },
    timings: { total_ms: 1.176 },
    resolution: null,
  };
}

export const mockDecisions: DecisionTrace[] = [
  trace(
    "LA-DEMO-0041",
    "AU0041",
    "Giftly Market",
    "gift_card",
    400,
    "decline",
    "Declined. This purchase is above your CHF 250 limit.",
    "Spending limits",
    "DECLINE",
    "OVER_PER_ORDER_LIMIT",
    250,
    2,
  ),
  trace(
    "LA-DEMO-0034",
    "AU0034",
    "RainThread",
    "clothing",
    138,
    "step_up",
    "RainThread is new to you. Approve this seller?",
    "Seller",
    "UNCERTAIN",
    "UNFAMILIAR_MERCHANT",
    120,
    5,
  ),
  trace(
    "LA-DEMO-0001",
    "AU0001",
    "Alpine Basket",
    "groceries",
    20,
    "approve",
    "Approved. This purchase is within your instruction.",
    "Spending limits",
    "PASS",
    null,
    20,
    9,
  ),
];

export const mockPending: PendingAuthorization[] = [
  {
    authorization_id: mockDecisions[1].ids.authorization_id,
    created_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + 120_000).toISOString(),
    trace: mockDecisions[1],
  },
];

export const mockStatus: EngineStatus = {
  connected: true,
  engine_mode: "deterministic",
  model_name: null,
  latest_margin_ms: 7824,
  active_run_id: "RUN-DEMO-0001",
  scenarios: [
    { scenario_id: "SCEN0000", name: "Connection check", purchase_count: 1 },
    { scenario_id: "SCEN0001", name: "Everyday groceries", purchase_count: 10 },
    { scenario_id: "SCEN0002", name: "Running shoes", purchase_count: 9 },
    { scenario_id: "SCEN0003", name: "Travel session", purchase_count: 12 },
    { scenario_id: "SCEN0004", name: "Monitor replacement", purchase_count: 13 },
  ],
};

export const mockPolicy: PolicyDraft = {
  draft_id: "TD-DEMO-0001",
  mandate_id: "TM-DEMO-0001",
  status: "active",
  instruction:
    "Buy one ordinary grocery item for CHF 20 or less from a shop I use regularly. Ask me when uncertain.",
  hard_rules: [
    {
      field: "authorization.billing_amount_chf",
      operator: "<=",
      value: 20,
      currency: "CHF",
      scope: "purchase",
    },
  ],
  uncertainty_policy: "ask",
  guidance: ["Use a shop the customer uses regularly."],
  open_questions: ["Ask the customer when seller familiarity cannot be established."],
};
