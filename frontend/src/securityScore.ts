import type { GuardFamily, GuardResult, GuardVerdict } from "./types";

export type EvaluationStatus = "evaluated" | "not_applicable" | "not_built" | "error";

export interface SecurityCoverage {
  ratio: number;
  evaluatedChecks: number;
  requiredChecks: number;
  notApplicableChecks: number;
  notBuiltChecks: number;
  errorChecks: number;
}

export interface FamilySecurityScore {
  family: GuardFamily;
  score: number | null;
  coverage: SecurityCoverage;
}

export interface SecurityScore {
  score: number | null;
  coverage: SecurityCoverage;
  families: FamilySecurityScore[];
  vetoedBy: string[];
}

const FAMILY_ORDER: GuardFamily[] = [
  "Spending limits",
  "Item and terms",
  "Seller",
  "Session",
  "Repeats and manipulation",
];

const POINTS: Partial<Record<GuardVerdict, number>> = {
  PASS: 100,
  UNCERTAIN: 50,
  STEP_UP: 50,
  DECLINE: 0,
};

export const evaluationStatus = (guard: GuardResult): EvaluationStatus => {
  if (guard.reason_code === "GUARD_NOT_BUILT") return "not_built";
  if (guard.reason_code === "GUARD_ERROR") return "error";
  if (guard.verdict === "SKIP") return "not_applicable";
  return "evaluated";
};

const mean = (values: number[]) =>
  values.length ? Math.round(values.reduce((total, value) => total + value, 0) / values.length) : null;

const coverage = (guards: GuardResult[]): SecurityCoverage => {
  const statuses = guards.map(evaluationStatus);
  const evaluatedChecks = statuses.filter((status) => status === "evaluated").length;
  const notApplicableChecks = statuses.filter((status) => status === "not_applicable").length;
  const notBuiltChecks = statuses.filter((status) => status === "not_built").length;
  const errorChecks = statuses.filter((status) => status === "error").length;
  const requiredChecks = guards.length - notApplicableChecks;
  const ratio = guards.length === 0 ? 0 : requiredChecks === 0 ? 1 : evaluatedChecks / requiredChecks;
  return { ratio, evaluatedChecks, requiredChecks, notApplicableChecks, notBuiltChecks, errorChecks };
};

const scoreFor = (guards: GuardResult[]) => mean(
  guards
    .filter((guard) => evaluationStatus(guard) === "evaluated")
    .flatMap((guard) => POINTS[guard.verdict] === undefined ? [] : [POINTS[guard.verdict] as number]),
);

// Presentation-only projection: decisions and guard results remain untouched.
export function securityScore(guards: GuardResult[]): SecurityScore {
  const families = FAMILY_ORDER.map((family) => {
    const familyGuards = guards.filter((guard) => guard.family === family);
    return { family, score: scoreFor(familyGuards), coverage: coverage(familyGuards) };
  });
  return {
    score: mean(families.flatMap((family) => family.score === null ? [] : [family.score])),
    coverage: coverage(guards),
    families,
    vetoedBy: guards
      .filter((guard) => evaluationStatus(guard) === "evaluated" && guard.verdict === "DECLINE")
      .map((guard) => guard.guard_id),
  };
}
