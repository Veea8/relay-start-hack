import { mockDecisions, mockPending, mockPolicy, mockStatus } from "./mockData";
import type {
  DecisionTrace,
  EngineStatus,
  PendingAuthorization,
  PolicyDraft,
  StreamEvent,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API !== "false";

const wait = (milliseconds = 240) =>
  new Promise<void>((resolve) => window.setTimeout(resolve, milliseconds));

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with status ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  async status(): Promise<EngineStatus> {
    if (USE_MOCK_API) {
      await wait();
      return structuredClone(mockStatus);
    }
    return request("/api/status");
  },

  async decisions(): Promise<DecisionTrace[]> {
    if (USE_MOCK_API) {
      await wait();
      return structuredClone(mockDecisions);
    }
    return request("/api/decisions");
  },

  async pending(): Promise<PendingAuthorization[]> {
    if (USE_MOCK_API) {
      await wait();
      return structuredClone(mockPending);
    }
    return request("/api/pending");
  },

  async compilePolicy(instruction: string): Promise<PolicyDraft> {
    if (USE_MOCK_API) {
      await wait(500);
      const amountMatch = instruction.match(/(?:CHF\s*)?(\d+(?:\.\d{1,2})?)/i);
      const limit = amountMatch ? Number(amountMatch[1]) : null;
      return {
        ...structuredClone(mockPolicy),
        draft_id: `TD-MOCK-${Date.now()}`,
        mandate_id: undefined,
        status: "draft",
        instruction,
        hard_rules: limit
          ? [{ field: "authorization.billing_amount_chf", operator: "<=", value: limit, currency: "CHF", scope: "purchase" }]
          : [],
        open_questions: limit ? [] : ["What is the maximum amount for one purchase?"],
      };
    }
    return request("/api/policy/compile", {
      method: "POST",
      body: JSON.stringify({ instruction }),
    });
  },

  async confirmPolicy(draftId: string): Promise<PolicyDraft> {
    if (USE_MOCK_API) {
      await wait();
      return { ...structuredClone(mockPolicy), draft_id: draftId, status: "active" };
    }
    return request("/api/policy/confirm", {
      method: "POST",
      body: JSON.stringify({ draft_id: draftId, confirmed: true }),
    });
  },

  async tightenPolicy(mandateId: string): Promise<PolicyDraft> {
    if (USE_MOCK_API) {
      await wait();
      return { ...structuredClone(mockPolicy), mandate_id: mandateId, uncertainty_policy: "decline" };
    }
    return request(`/api/policy/${mandateId}`, {
      method: "PATCH",
      body: JSON.stringify({ uncertainty_policy: "decline" }),
    });
  },

  async revokePolicy(mandateId: string): Promise<void> {
    if (USE_MOCK_API) return wait();
    return request(`/api/policy/${mandateId}`, { method: "DELETE" });
  },

  async startRun(scenarioId: string, mandateId: string): Promise<{ run_id: string }> {
    if (USE_MOCK_API) {
      await wait();
      return { run_id: `RUN-${scenarioId}-MOCK` };
    }
    return request("/api/run/start", {
      method: "POST",
      body: JSON.stringify({ scenario_id: scenarioId, mandate_id: mandateId }),
    });
  },

  async resolve(authorizationId: string, decision: "approve" | "decline"): Promise<void> {
    if (USE_MOCK_API) return wait();
    return request(`/api/resolve/${authorizationId}`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    });
  },
};

export function connectEventStream(onEvent: (event: StreamEvent) => void, onState: (connected: boolean) => void) {
  if (USE_MOCK_API) {
    onState(true);
    return () => undefined;
  }

  const eventSource = new EventSource(`${API_BASE_URL}/api/stream`);
  const handle = (message: MessageEvent<string>) => {
    try {
      onEvent(JSON.parse(message.data) as StreamEvent);
    } catch {
      // A malformed event is ignored; the next valid event keeps the live view current.
    }
  };
  eventSource.onopen = () => onState(true);
  eventSource.onmessage = handle;
  eventSource.onerror = () => onState(false);
  return () => eventSource.close();
}
