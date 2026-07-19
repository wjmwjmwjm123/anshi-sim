import type {
  AudienceRequest, AudienceResponse,
  CouncilEvent, CouncilRequest,
  DecreeResponse, DirectiveRequest, DirectiveResponse,
  EventChoiceRequest, EventChoiceResponse,
  ArmyMoveRequest, ArmyMoveResponse,
  ModelConfigResponse, ModelConfigUpdate,
  Order, PolicySelectRequest, PolicySelectResponse,
  SaveSlot, SecretEdictRequest, Snapshot, TurnRequest, TurnResponse,
} from "./types";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || response.statusText);
  }
  return response.json();
}

export async function stream<T>(
  path: string,
  body: object,
  onEvent: (event: T) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok || !response.body) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || response.statusText);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6)) as T;
          onEvent(event);
        } catch {
          // ignore malformed SSE lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export const api = {
  snapshot: () => request<Snapshot>("/api/snapshot"),

  turn: (order: Order) => request<TurnResponse>("/api/turn", { method: "POST", body: JSON.stringify({ order } as TurnRequest) }),

  reset: () => request<Snapshot>("/api/reset", { method: "POST" }),

  directives: {
    add: (draft: DirectiveRequest) => request<DirectiveResponse>("/api/directives", { method: "POST", body: JSON.stringify(draft) }),
    remove: (id: number) => request<DirectiveResponse>(`/api/directives/${id}`, { method: "DELETE" }),
  },

  decrees: {
    freeform: (text: string) => request<DecreeResponse>("/api/decrees/freeform", { method: "POST", body: JSON.stringify({ text }) }),
    confirm: (id: number) => request<{ accepted: boolean; detail?: string; decree?: any }>(`/api/decrees/${id}/confirm`, { method: "POST" }),
  },

  events: {
    choose: (choice: string) => request<EventChoiceResponse>("/api/events/choice", { method: "POST", body: JSON.stringify({ choice } as EventChoiceRequest) }),
  },

  secretEdicts: {
    send: (draft: SecretEdictRequest) => request<any>("/api/secret-edicts", { method: "POST", body: JSON.stringify(draft) }),
  },

  armies: {
    move: (draft: ArmyMoveRequest) => request<ArmyMoveResponse>("/api/armies/move", { method: "POST", body: JSON.stringify(draft) }),
  },

  policies: {
    select: (policy_id: string) => request<PolicySelectResponse>("/api/policies/select", { method: "POST", body: JSON.stringify({ policy_id } as PolicySelectRequest) }),
  },

  audience: {
    ask: (draft: AudienceRequest) => request<AudienceResponse>("/api/audience", { method: "POST", body: JSON.stringify(draft) }),
    stream: (draft: AudienceRequest, onEvent: (event: any) => void, signal?: AbortSignal) =>
      stream<any>("/api/audience/stream", draft, onEvent, signal),
  },

  council: {
    stream: (draft: CouncilRequest, onEvent: (event: CouncilEvent) => void, signal?: AbortSignal) =>
      stream<CouncilEvent>("/api/council/stream", draft, onEvent, signal),
  },

  resolve: {
    stream: (onEvent: (event: any) => void, signal?: AbortSignal) =>
      stream<any>("/api/resolve/stream", {}, onEvent, signal),
  },

  saves: {
    list: () => request<{ slots: SaveSlot[] }>("/api/saves"),
    save: (slot_id: number, name: string) => request<{ slots: SaveSlot[] }>("/api/saves", { method: "POST", body: JSON.stringify({ slot_id, name }) }),
    load: (id: number) => request<{ loaded: true; snapshot: Snapshot }>(`/api/saves/${id}/load`, { method: "POST" }),
  },

  modelConfig: {
    get: () => request<ModelConfigResponse>("/api/model-config"),
    update: (payload: ModelConfigUpdate) => request<ModelConfigResponse & { detail?: string }>("/api/model-config", { method: "POST", body: JSON.stringify(payload) }),
  },
};
