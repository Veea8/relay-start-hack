import { describe, expect, it } from "vitest";
import { evaluationStatus, securityScore } from "./securityScore";
import type { GuardFamily, GuardResult, GuardVerdict } from "./types";

const guard = (
  guardId: string,
  family: GuardFamily,
  verdict: GuardVerdict,
  reasonCode: string | null = null,
): GuardResult => ({
  guard_number: 1,
  guard_id: guardId,
  family,
  verdict,
  reason_code: reasonCode,
  evidence: [],
  signal: null,
  note: null,
  customer_message: null,
  elapsed_ms: 0,
});

describe("securityScore", () => {
  it("separates an inapplicable check from checks that are not built or failed", () => {
    expect(evaluationStatus(guard("skip", "Session", "SKIP"))).toBe("not_applicable");
    expect(evaluationStatus(guard("todo", "Session", "SKIP", "GUARD_NOT_BUILT"))).toBe("not_built");
    expect(evaluationStatus(guard("broken", "Session", "UNCERTAIN", "GUARD_ERROR"))).toBe("error");
  });

  it("balances families, reports coverage and preserves a decline veto", () => {
    const result = securityScore([
      guard("limit_1", "Spending limits", "PASS"),
      guard("limit_2", "Spending limits", "PASS"),
      guard("seller_review", "Seller", "STEP_UP"),
      guard("seller_block", "Seller", "DECLINE"),
      guard("not_relevant", "Session", "SKIP"),
      guard("not_built", "Session", "SKIP", "GUARD_NOT_BUILT"),
    ]);

    expect(result.score).toBe(63);
    expect(result.coverage).toMatchObject({
      ratio: 0.8,
      evaluatedChecks: 4,
      requiredChecks: 5,
      notApplicableChecks: 1,
      notBuiltChecks: 1,
    });
    expect(result.vetoedBy).toEqual(["seller_block"]);
  });
});
