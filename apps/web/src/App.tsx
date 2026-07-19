import React from "react";
import {
  AlertTriangle, CirclePlay, Gavel, ScrollText, Stamp,
} from "lucide-react";
import type { Order, Snapshot, Tab } from "./types";
import { api } from "./api";
import { CampaignRail, SideNav, TopBar } from "./components/layout";
import {
  AudienceDrawer, CouncilModal, DecreeReview, EdictComposer,
  EventDecision, MultiModelDrawer,
} from "./components/panels";
import {
  ArmyCommandView, HistoryView, ImperialCourt, Overview, PolicyFocusViewRich,
  RegionsView, ReportCenter, StartScreen,
} from "./components/screens";

export default function App() {
  const [snap, setSnap] = React.useState<Snapshot | null>(null);
  const [entered, setEntered] = React.useState(false);
  const [tab, setTab] = React.useState<Tab>("court");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState("");
  const [audience, setAudience] = React.useState<any>(null);
  const [decree, setDecree] = React.useState<any>(null);
  const [modelOpen, setModelOpen] = React.useState(false);
  const [councilOpen, setCouncilOpen] = React.useState(false);
  const [edictOpen, setEdictOpen] = React.useState(false);
  const [eventOpen, setEventOpen] = React.useState(false);
  const [resolution, setResolution] = React.useState<any>(null);
  const [orderReport, setOrderReport] = React.useState<any>(null);

  const load = React.useCallback(async () => {
    const data = await api.snapshot();
    setSnap(data);
  }, []);

  React.useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [load]);

  const act = async (fn: () => Promise<any>) => {
    setBusy(true);
    setError("");
    try {
      const data = await fn();
      if (data && data.accepted === false) {
        throw new Error(data.detail || "操作失败");
      }
      await load();
      return data;
    } catch (e) {
      setError(e instanceof Error ? e.message : "操作失败");
    } finally {
      setBusy(false);
    }
  };

  const order = async (value: Order) => {
    const data = await act(() => api.turn(value));
    if (data) setOrderReport(data);
  };
  const add = (draft: any) => act(() => api.directives.add(draft));
  const remove = (id: number) => act(() => api.directives.remove(id));

  const resolve = async () => {
    setBusy(true);
    setError("");
    try {
      const controller = new AbortController();
      let reportText = "";
      await api.resolve.stream(
        (d: any) => {
          if (d.requires_choice) {
            setEventOpen(true);
            setBusy(false);
            controller.abort();
            return;
          }
          if (d.error) {
            setError(d.error);
            setBusy(false);
            controller.abort();
            return;
          }
          if (d.type === "snapshot") {
            setEventOpen(false);
            setResolution({ ...d.data.data, narration: d.data.narration, report: "", reportTitle: "", campaign: d.data.campaign_result, gazette: d.data.gazette || "" });
            setTab("history");
          }
          if (d.type === "report_start") {
            reportText = "";
            setResolution((prev: any) => (prev ? { ...prev, report: "", reportTitle: d.title || "月末奏章" } : prev));
          }
          if (d.type === "report_delta") {
            reportText += d.delta;
            setResolution((prev: any) => (prev ? { ...prev, report: reportText } : prev));
          }
          if (d.type === "report_end") {
            setResolution((prev: any) => (prev ? { ...prev, report: d.report } : prev));
          }
        },
        controller.signal,
      );
    } catch {
      // stream aborted or ended
    } finally {
      setBusy(false);
      await load();
    }
  };

  const queueEventChoice = async (choice: string) => {
    const data = await act(() => api.events.choose(choice));
    if (data?.accepted) setEventOpen(false);
  };

  const secret = (draft: any) => act(() => api.secretEdicts.send(draft));

  const freeform = async (text: string) => {
    const data = await act(() => api.decrees.freeform(text));
    if (data) {
      setDecree(data.decree);
      setEdictOpen(false);
    }
  };

  const confirmDecree = async (id: number) => {
    const data = await act(() => api.decrees.confirm(id));
    if (data?.accepted) setDecree(null);
  };

  const reset = async () => {
    await act(() => api.reset());
    setResolution(null);
    setTab("court");
    setEntered(true);
  };

  const loadSlot = async (id: number) => {
    await act(() => api.saves.load(id));
    setEntered(true);
    setTab("court");
  };

  const saveSlot = async () => {
    const name = window.prompt("请输入存档名称", `第${snap?.progress.total_turn || 1}回合存档`);
    if (name) await act(() => api.saves.save(Date.now() % 1000000, name));
  };

  const moveArmy = (army_id: string, destination: string) => act(() => api.armies.move({ army_id, destination }));

  const selectPolicy = async (policy_id: string) => {
    const data = await act(() => api.policies.select(policy_id));
    if (data?.accepted === false) setError(data.detail || "国策暂不可用");
  };

  if (!snap) return <main className="loading">正在展开天下图册…</main>;
  if (!entered) return <StartScreen slots={snap.save_slots || []} onNew={reset} onLoad={loadSlot} />;

  const s = snap.state;
  const m = snap.management;
  const pendingDecision = snap.progress.pending_event_choice;
  const TurnActionIcon = snap.progress.active_event && !pendingDecision ? Gavel : m.directives.length || pendingDecision ? Stamp : CirclePlay;

  const roleConfigs = snap.runtime["模型职责"] || {};
  const configuredRoles = Object.entries(roleConfigs).filter(([, config]: [string, any]) => config.configured);
  const modelSummary = configuredRoles.map(([id, config]: [string, any]) =>
    `${id === "chat" ? "人物" : id === "simulation" ? "推演" : "文书"}：${config.model || "已配置"}`,
  ).join(" / ") || "使用中文模板";

  const urgentIssueCount = Object.values(m.issues).filter((i: any) => i.tension >= 70).length;

  return (
    <main className="game-shell">
      <TopBar
        state={s}
        management={m}
        progress={snap.progress}
        modelSummary={modelSummary}
        configuredCount={configuredRoles.length}
        onOpenModel={() => setModelOpen(true)}
        onOpenCouncil={() => setCouncilOpen(true)}
        onSave={saveSlot}
        onExit={() => setEntered(false)}
        onReset={reset}
      />
      <CampaignRail acts={snap.acts} currentActId={s.act_id} />
      <div className="game-body">
        <SideNav tab={tab} onTabChange={setTab} urgentIssueCount={urgentIssueCount} />
        <div className="main-workspace">
          {tab === "court" && <ImperialCourt snap={snap} onAudience={setAudience} />}
          {tab === "overview" && <Overview snap={snap} onOrder={order} orderBusy={busy} report={orderReport} />}
          {tab === "map" && <RegionsView snap={snap} />}
          {tab === "army" && <ArmyCommandView snap={snap} onMove={moveArmy} onDirective={add} />}
          {tab === "memorials" && <ReportCenter snap={snap} />}
          {tab === "policy" && <PolicyFocusViewRich snap={snap} onSelect={selectPolicy} />}
          {tab === "history" && <HistoryView state={s} resolution={resolution} />}
        </div>
      </div>

      {error && (
        <div className="toast-error">
          <AlertTriangle size={16} />{error}
        </div>
      )}

      <button className="edict-launch" onClick={() => setEdictOpen(true)} title="拟写诏书" aria-label="拟写诏书">
        <ScrollText aria-hidden="true" />
        <small>拟诏</small>
      </button>
      <button
        className="turn-advance"
        onClick={() => (snap.progress.active_event && !pendingDecision ? setEventOpen(true) : resolve())}
        disabled={busy}
        title={snap.progress.active_event && !pendingDecision ? "御前裁决" : m.directives.length || pendingDecision ? "颁诏并推进" : "推进回合"}
      >
        <TurnActionIcon aria-hidden="true" />
        <small>
          {snap.progress.active_event && !pendingDecision
            ? "御前裁决"
            : m.directives.length || pendingDecision
            ? `颁诏${pendingDecision ? "并裁决" : ""}`
            : "推进回合"}
        </small>
      </button>

      {eventOpen && snap.progress.active_event && (
        <div className="event-overlay">
          <EventDecision
            event={snap.progress.active_event}
            onChoose={queueEventChoice}
            onClose={() => setEventOpen(false)}
            busy={busy}
          />
        </div>
      )}
      {edictOpen && (
        <EdictComposer
          onClose={() => setEdictOpen(false)}
          onSubmit={freeform}
          busy={busy}
          decision={pendingDecision}
          issued={(snap.conversation.freeform_decrees || []).filter((item: any) => item.status === "已颁行")}
        />
      )}
      {audience && (
        <AudienceDrawer
          character={audience}
          office={snap.management.characters[audience.id]?.office}
          conversation={snap.conversation}
          onClose={() => setAudience(null)}
          onSecret={secret}
        />
      )}
      {decree && <DecreeReview decree={decree} onConfirm={confirmDecree} onClose={() => setDecree(null)} />}
      {councilOpen && <CouncilModal snap={snap} onClose={() => setCouncilOpen(false)} />}
      {modelOpen && <MultiModelDrawer onClose={() => setModelOpen(false)} onSaved={load} />}

    </main>
  );
}
