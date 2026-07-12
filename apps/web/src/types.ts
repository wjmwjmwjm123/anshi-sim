import type { LucideIcon } from "lucide-react";

export type Tab = "court" | "overview" | "map" | "army" | "memorials" | "policy" | "history";
export type Order = "hold" | "verify" | "reconcile" | "constrain" | "prepare_retreat" | "sally";
export type DirectiveKind = "relief" | "tax" | "supply" | "mobilize" | "fortify" | "investigate" | "appoint" | "mediate";
export type Scene = "朝堂" | "密诏" | "远奏";
export type CoreState = any;

export type FinanceState = {
  cash: number;
  grain: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_grain: number;
};

export type RegionRuntime = {
  name: string;
  support: number;
  unrest: number;
  tax_rate: number;
  fortification: number;
};

export type ArmyRuntime = {
  name: string;
  region: string;
  strength: number;
  fit_strength: number;
  supply: number;
  morale: number;
};

export type IssueRuntime = {
  title: string;
  tension: number;
  progress: number;
  status: string;
  assignee: string;
};

export type CharacterRuntime = {
  name: string;
  office: string;
  loyalty: number;
  ability: number;
  status: string;
};

export type QueuedDirective = {
  id: number;
  kind: DirectiveKind;
  target: string;
  amount: number;
  subject: string;
};

export type Management = {
  turn: number;
  finance: FinanceState;
  regions: Record<string, RegionRuntime>;
  armies: Record<string, ArmyRuntime>;
  issues: Record<string, IssueRuntime>;
  characters: Record<string, CharacterRuntime>;
  directives: QueuedDirective[];
};

export type Catalog = {
  regions: any[];
  armies: any[];
  characters: any[];
  initial_finance: any;
  ongoing_issues: any[];
  acts: any[];
  evidence_legend: Record<string, string>;
};

export type Snapshot = {
  state: CoreState;
  management: Management;
  catalog: Catalog;
  acts: any[];
  progress: any;
  runtime: Record<string, any>;
  conversation: any;
  strategy: any;
  agent_runs: any[];
  save_slots: any[];
};

export type NavItem = { id: Tab; label: string; Icon: LucideIcon };
export type OrderMeta = { id: Order; title: string; note: string; gain: string; risk: string; Icon: LucideIcon };
export type DirectiveMeta = Record<DirectiveKind, { label: string; domain: "regions" | "armies" | "issues" | "characters" }>;
export type ArmyAction = { id: string; label: string; note: string; asset: string; Icon: LucideIcon };

export type AudienceRequest = { character_id: string; topic?: string; scene?: string };
export type AudienceResponse = { accepted: boolean; reply?: string; detail?: string; model_used?: boolean };

export type CouncilRequest = {
  character_ids: string[];
  topic?: string;
  round_no?: number;
  previous_minutes?: string;
  emperor_remark?: string;
};

export type CouncilEvent =
  | { type: "council_start"; topic: string; round: number }
  | { type: "speech_start"; name: string; round: number }
  | { type: "speech_delta"; name: string; delta: string }
  | { type: "speech_end"; name: string; reply: string; round: number }
  | { type: "minutes"; round: number | "final"; text: string }
  | { type: "emperor_options"; is_final: boolean }
  | { done: true }
  | { error: string };

export type TurnRequest = { order: Order };
export type TurnResponse = any;

export type ResolveEvent =
  | { type: "snapshot"; data: any }
  | { type: "gazette_start" }
  | { type: "gazette_delta"; delta: string }
  | { type: "gazette_end"; gazette: string }
  | { requires_choice: true; event: any }
  | { error: string }
  | { done: true };

export type DirectiveRequest = { kind: DirectiveKind; target: string; amount?: number; subject?: string };
export type DirectiveResponse = { directive: QueuedDirective; directives: QueuedDirective[] };

export type ArmyMoveRequest = { army_id: string; destination: string };
export type ArmyMoveResponse = any;

export type PolicySelectRequest = { policy_id: string };
export type PolicySelectResponse = any;

export type DecreeResponse = { decree: any };

export type SaveSlot = { slot_id: number; name: string; updated_at?: string; act: number; turn: number; year: number; month: number };

export type ModelConfigResponse = { roles?: Record<string, any>; base_url?: string; model?: string; configured?: boolean; detail?: string };
export type ModelConfigUpdate = { role?: string; api_key?: string; base_url?: string; model?: string };

export type SecretEdictRequest = { character_id: string; text: string; purpose?: string };

export type EventChoiceRequest = { choice: string };
export type EventChoiceResponse = { accepted: boolean; pending_event_choice?: any; detail?: string };
