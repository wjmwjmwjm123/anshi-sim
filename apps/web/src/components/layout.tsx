import { LogOut, MessagesSquare, RotateCcw, Save, Settings } from "lucide-react";
import type { Tab } from "../types";
import { Metric } from "./shared";
import { nav } from "../constants";

export function TopBar({
  state,
  management,
  progress,
  modelSummary,
  configuredCount,
  onOpenModel,
  onOpenCouncil,
  onSave,
  onExit,
  onReset,
}: {
  state: any;
  management: any;
  progress: any;
  modelSummary: string;
  configuredCount: number;
  onOpenModel: () => void;
  onOpenCouncil: () => void;
  onSave: () => void;
  onExit: () => void;
  onReset: () => void;
}) {
  return (
    <header className="topbar">
      <div className="brand">
        <span className="seal">唐</span>
        <div>
          <h1>安史之乱</h1>
          <p>中唐续命 · 国家军政中枢</p>
        </div>
      </div>
      <div className="top-metrics">
        <Metric label="皇威" value={state.central_prestige} hint="诏令执行力·受朝堂派系与军事成败影响" />
        <Metric label="军势" value={state.military_power} hint="唐军总战力·受潼关战局与节度使调度影响" />
        <Metric label="民心" value={state.popular_support} hint="百姓安定度·受赋税赈济与战乱波及影响" />
        <Metric label="现银" value={management.finance.cash} hint={`月入${management.finance.monthly_income}·月支${management.finance.monthly_expenses}·天宝岁入约5700万贯`} />
        <Metric label="粮储" value={management.finance.grain} hint={`月粮${management.finance.monthly_grain}·天宝仓储约一万万石`} />
      </div>
      <div className="date-block">
        <span>{state.phase} · 第 {progress.total_turn} 回合 · {progress.year}年{progress.month}月</span>
        <button className="model-status" onClick={onOpenModel} title={modelSummary}>
          <Settings aria-hidden="true" />
          <span>
            <b>模型 {configuredCount}/3</b>
            <small>{modelSummary}</small>
          </span>
        </button>
      </div>
      <div className="header-actions">
        <button onClick={onOpenCouncil} title="召集群议" aria-label="召集群议">
          <MessagesSquare />
        </button>
        <button onClick={onSave} title="另存游戏" aria-label="另存游戏">
          <Save />
        </button>
        <button onClick={onExit} title="返回主菜单" aria-label="返回主菜单">
          <LogOut />
        </button>
        <button onClick={onReset} title="重新开始" aria-label="重新开始">
          <RotateCcw />
        </button>
      </div>
    </header>
  );
}

export function SideNav({
  tab,
  onTabChange,
  urgentIssueCount,
}: {
  tab: Tab;
  onTabChange: (tab: Tab) => void;
  urgentIssueCount: number;
}) {
  return (
    <nav className="side-nav">
      {nav.map(({ id, label, Icon }) => (
        <button key={id} className={tab === id ? "active" : ""} onClick={() => onTabChange(id)} title={label}>
          <img
            className="nav-gen-icon"
            src={`/assets/generated/nav/${id}.webp`}
            alt={label}
            loading="lazy"
            onError={(e) => { const t = e.target as HTMLImageElement; t.style.display = "none"; const sib = t.nextElementSibling as HTMLElement; if (sib) sib.style.display = ""; }}
          />
          <Icon size={18} className="nav-fallback-icon" style={{ display: "none" }} />
          <span>{label}</span>
          {id === "memorials" && urgentIssueCount > 0 && <b>{urgentIssueCount}</b>}
        </button>
      ))}
    </nav>
  );
}

export function CampaignRail({ acts, currentActId }: { acts: any[]; currentActId: string }) {
  return (
    <div className="campaign-rail">
      {acts.map((a: any, i: number) => (
        <div key={a.id} className={a.id === currentActId ? "current" : ""}>
          <span>0{i + 1}</span>
          <b>{a.title}</b>
          <small>{a.date_range}</small>
        </div>
      ))}
    </div>
  );
}
