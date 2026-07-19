import React from "react";
import {
  AlertTriangle, BookOpen, CheckCircle2, CirclePlay, Clock3, Eye,
  LockKeyhole, TrendingDown, TrendingUp, Wheat,
} from "lucide-react";
import type { Order, OrderMeta, Snapshot } from "../types";
import { CampaignMap, Evidence, Meter, Metric, Portrait, SectionHead } from "./shared";
import WorldMap from "../WorldMap";
import { armyActions, cn, directiveMeta, focusBranches, orders, policyEffects } from "../constants";

export function StartScreen({ slots, onNew, onLoad }: { slots: any[]; onNew: () => void; onLoad: (id: number) => void }) {
  const auto = slots.find((item) => item.slot_id === 0);
  return (
    <main className="start-screen">
      <div className="start-backdrop">
        <div className="era-prologue">
          <span>天宝十五载 · 公元七五六年</span>
          <h2>渔阳鼙鼓动地来，潼关以东尽为战场</h2>
          <p>安禄山据洛阳称帝，河北郡县反复。哥舒翰统大军扼守潼关，长安朝堂却催战不止。粮道、军令、皇权与民心，都将在数月内决定大唐能否延续。</p>
          <ol>
            <li>稳住潼关军令</li>
            <li>核验前线情报</li>
            <li>保住关中钱粮</li>
          </ol>
        </div>
        <span className="start-seal">唐</span>
        <h1>安史之乱</h1>
        <p>中唐续命</p>
        <small>天宝十五载，潼关军报抵京。你将通过召见、密诏与御笔诏书，重新推动这台失序的国家机器。</small>
        <div className="start-actions">
          {auto && (
            <button className="primary" onClick={() => onLoad(0)}>
              <b>继续游戏</b>
              <span>{auto.year}年{auto.month}月 · 第{auto.turn}回合</span>
            </button>
          )}
          <button onClick={onNew}>
            <b>开始新游戏</b>
            <span>从潼关危局开始</span>
          </button>
        </div>
        {slots.filter((item) => item.slot_id !== 0).length > 0 && (
          <div className="save-list">
            <h2>载入存档</h2>
            {slots
              .filter((item) => item.slot_id !== 0)
              .map((slot) => (
                <button key={slot.slot_id} onClick={() => onLoad(slot.slot_id)}>
                  <b>{slot.name}</b>
                  <span>{slot.year}年{slot.month}月 · 第{slot.turn}回合</span>
                </button>
              ))}
          </div>
        )}
      </div>
    </main>
  );
}

export function ImperialCourt({ snap, onAudience }: { snap: Snapshot; onAudience: (character: any) => void }) {
  const [showAll, setShowAll] = React.useState(false);
  const activeChars = snap.catalog.characters.filter(
    (character: any) =>
      snap.management.characters[character.id]?.status === "active" &&
      !["enemy_only", "future_enemy", "player_character"].includes(character.audience_status),
  );
  const visible = showAll ? activeChars : activeChars.slice(0, 18);
  const total = activeChars.length;
  const left = visible.filter((character: any, index: number) => (character.court_side ? character.court_side === "left" : index % 2 === 0)
  );
  const right = visible.filter((character: any, index: number) => (character.court_side ? character.court_side === "right" : index % 2 === 1)
  );
  const recent = Object.entries(snap.conversation.chats || {})
    .flatMap(([id, messages]: any) => messages.slice(-1).map((message: any) => ({ ...message, id })))
    .sort((a: any, b: any) => b.turn - a.turn)
    .slice(0, 4);
  const group = (character: any) =>
    character.institution ||
    (["中书", "门下", "尚书", "吏部", "户部", "礼部", "兵部", "刑部", "工部"].find((name) => character.identity.includes(name)) || "朝臣");
  const statusCn: Record<string, string> = { active: "在朝", offstage: "未登场", dismissed: "已罢黜", imprisoned: "下狱", exiled: "流放", retired: "致仕", dead: "已故" };
  const rank = (characters: any[], side: string) => (
    <div className={`court-rank ${side}`}>
      {characters.map((character: any) => {
        const ch = snap.management.characters[character.id];
        const st = ch?.status;
        return (
          <button key={character.id} onClick={() => onAudience(character)} className={st !== "active" ? "offstage" : ""}>
            <Portrait character={character} />
            <span>
              <em>{group(character)}{st && st !== "active" ? ` · ${statusCn[st] || st}` : ""}</em>
              <b>{character.name}</b>
              <small>{ch?.office || character.identity}</small>
            </span>
          </button>
        );
      })}
    </div>
  );
  return (
    <section className="imperial-court">
      <SectionHead eyebrow="紫宸殿常朝" title="百官奏对" extra={
        <span>
          {total} 人在册
          {total > 18 && (
            <button className="toggle-all" onClick={() => setShowAll(!showAll)}>
              {showAll ? "收起" : "查看全部"}
            </button>
          )}
        </span>
      } />
      <div className="court-floor">
        {rank(left, "east")}
        <div className="throne-axis">
          <span className="throne-seal">唐</span>
          <small>天子御座</small>
          <h3>{snap.progress.active_event ? "军国急务" : "今日朝仪"}</h3>
          {snap.progress.active_event ? (
            <article>
              <b>{snap.progress.active_event.title}</b>
              <p>{snap.progress.active_event.summary}</p>
              <em>颁诏推进时须先御前裁断</em>
            </article>
          ) : (
            <p>群臣分班候旨，可单独召见，亦可由右上“议”召集多人廷议。</p>
          )}
          <div>
            <span>中书取旨</span>
            <span>门下审覆</span>
            <span>尚书施行</span>
          </div>
        </div>
        {rank(right, "west")}
      </div>
      <footer className="court-notes">
        <div>
          <b>近来奏对</b>
          {recent.length ? (
            recent.map((item: any, idx: number) => (
              <p key={`${item.id}-${item.turn}-${idx}`}>
                <strong>{snap.catalog.characters.find((c: any) => c.id === item.id)?.name || "臣下"}</strong>
                {item.text}
              </p>
            ))
          ) : (
            <p>尚无奏对记录。</p>
          )}
        </div>
        <div>
          <b>三省六部</b>
          <p>中书草诏、门下封驳、尚书统六部执行；人物会依机构职责和自身立场参与朝议。</p>
          <small>密诏 {snap.progress.secret_edicts.length} 道 · 君臣关系 {Object.keys(snap.conversation.relationships || {}).length} 组</small>
        </div>
      </footer>
    </section>
  );
}

export function CourtView({ snap, onAudience }: { snap: Snapshot; onAudience: (character: any) => void }) {
  const visible = snap.catalog.characters.filter(
    (character: any) =>
      snap.management.characters[character.id]?.status === "active" &&
      !["enemy_only", "future_enemy", "player_character"].includes(character.audience_status),
  );
  return (
    <section>
      <SectionHead eyebrow="紫宸殿" title="召见与远奏" extra={<span>{visible.length} 人可奏对</span>} />
      <div className="court-list">
        {visible.map((character: any) => (
          <button key={character.id} onClick={() => onAudience(character)}>
            <Portrait character={character} />
            <div>
              <b>{character.name}</b>
              <small>{snap.management.characters[character.id]?.office || character.identity}</small>
              <p>{character.public_stance}</p>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

export function ThroneRoom({ snap, onAudience }: { snap: Snapshot; onAudience: (character: any) => void }) {
  const visible = snap.catalog.characters
    .filter(
      (character: any) =>
        snap.management.characters[character.id]?.status === "active" &&
        !["enemy_only", "future_enemy", "player_character"].includes(character.audience_status),
    )
    .slice(0, 12);
  const recent = Object.entries(snap.conversation.chats || {})
    .flatMap(([id, messages]: any) => messages.slice(-2).map((message: any) => ({ ...message, id })))
    .sort((a: any, b: any) => b.turn - a.turn)
    .slice(0, 5);
  return (
    <div className="throne-room">
      <section className="throne-main">
        <SectionHead eyebrow="紫宸殿奏对" title="今日召见" extra={<span>{visible.length} 人候旨</span>} />
        <div className="minister-bench">
          {visible.map((character: any) => (
            <button key={character.id} onClick={() => onAudience(character)}>
              <Portrait character={character} />
              <b>{character.name}</b>
              <small>{snap.management.characters[character.id]?.office || character.identity}</small>
              <p>{character.public_stance}</p>
            </button>
          ))}
        </div>
      </section>
      <aside className="court-sidebar">
        <SectionHead eyebrow="本回合" title="待议军国事" />
        {snap.progress.active_event && (
          <article className="current-matter">
            <b>{snap.progress.active_event.title}</b>
            <p>{snap.progress.active_event.summary}</p>
            <small>可先召见相关人物，不必立即选择。</small>
          </article>
        )}
        <SectionHead eyebrow="近来奏对" title="君臣记录" />
        {recent.length ? (
          recent.map((item: any, index: number) => (
            <article className="recent-chat" key={`${item.id}-${index}`}>
              <b>{snap.catalog.characters.find((c: any) => c.id === item.id)?.name || "臣下"}</b>
              <p>{item.text}</p>
              <small>{item.scene} · 第{item.turn}回合</small>
            </article>
          ))
        ) : (
          <p className="empty-note">尚未召见人物。</p>
        )}
        <SectionHead eyebrow="跨回合" title="密诏与承诺" />
        <p className="compact-note">密诏 {snap.progress.secret_edicts.length} 道 · 人物关系 {Object.keys(snap.conversation.relationships || {}).length} 组</p>
      </aside>
    </div>
  );
}

export function Overview({ snap, onOrder, orderBusy, report }: { snap: Snapshot; onOrder: (order: Order) => void; orderBusy: boolean; report: any }) {
  const { state, management, catalog: fullCatalog } = snap;
  const frontlineIds = new Set([
    "changan", "tongguan", "lingbao", "shanjun", "luoyang", "hedong", "shuofang", "fanyang", "changshan", "pingyuan", "suiyang",
  ]);
  const catalog = { ...fullCatalog, regions: fullCatalog.regions.filter((region: any) => frontlineIds.has(region.id)) };
  return (
    <>
      <SituationPanel snap={snap} />
      <ObjectivePanel snap={snap} />
      <div className="overview-grid">
        <section className="map-panel">
          <SectionHead eyebrow="天下形势" title="关中与河北战局" extra={<b>{Object.keys(management.armies).length} 支军队在册</b>} />
          <CampaignMap data={catalog} management={management} strategy={snap.strategy} />
        </section>
        <aside className="issues-panel">
          <SectionHead eyebrow="御前急务" title="待决事项" extra={<AlertTriangle size={18} />} />
          {Object.entries(management.issues)
            .slice(0, 6)
            .map(([id, issue]: [string, any]) => (
              <div className="issue-row" key={id}>
                <div>
                  <b>{issue.title}</b>
                  <span>{issue.assignee ? `承办：${management.characters[issue.assignee]?.name || issue.assignee}` : "尚未责成"}</span>
                </div>
                <strong>{issue.tension}</strong>
                <Meter value={issue.tension} danger />
              </div>
            ))}
        </aside>
        <section className="intel-panel">
          <SectionHead eyebrow="御史台与军报" title="已知情报" extra={<Eye size={18} />} />
          {state.intel_claims.slice(0, 4).map((claim: any) => (
            <article key={claim.id}>
              <div>
                <b>{claim.source}</b>
                <strong>{claim.confidence}%</strong>
              </div>
              <p>{claim.summary}</p>
              <small>{claim.age_days} 日前 · {claim.independent ? "独立来源链" : "单一来源链"} · {cn(claim.status)}</small>
            </article>
          ))}
        </section>
        <section className="emergency-panel">
          <SectionHead eyebrow="潼关专案" title="即时军令" extra={<span>{state.tongguan_status}</span>} />
          <div className="emergency-orders">
            {orders.map((orderMeta: OrderMeta) => {
              const { Icon, ...order } = orderMeta;
              return (
                <button key={order.id} onClick={() => onOrder(order.id)} disabled={orderBusy || state.ended}>
                  <Icon className="order-icon" aria-hidden="true" />
                  <b>{order.title}</b>
                  <small>{order.note}</small>
                  <span>利：{order.gain}</span>
                  <em>险：{order.risk}</em>
                </button>
              );
            })}
          </div>
          {report && (
            <article className="field-report">
              <span>尚书省兵部递报</span>
              <h3>{report.headline}</h3>
              <p>{report.narrative}</p>
              {report.reasons?.map((reason: string) => (
                <small key={reason}>{reason}</small>
              ))}
            </article>
          )}
          {state.ended && <p className="locked-note">潼关篇已结，国家经营与下一章仍可继续。</p>}
        </section>
      </div>
    </>
  );
}

export function RegionsView({ snap }: { snap: Snapshot }) {
  const [selected, setSelected] = React.useState("changan");
  const region = snap.catalog.regions.find((item: any) => item.id === selected);
  const runtime = snap.management.regions[selected];
  return (
    <div className="split-view">
      <section>
        <SectionHead eyebrow="山河地理" title="十六地区" />
        <WorldMap data={snap.catalog} management={snap.management} strategy={snap.strategy} selected={selected} onSelect={setSelected} />
      </section>
      <aside className="detail-sheet">
        <SectionHead eyebrow="地区档案" title={region?.name || "选择地区"} extra={region && <Evidence value={region.evidence_status} />} />
        {region && runtime && (
          <>
            <dl>
              <dt>控制者</dt>
              <dd>{cn(region.controller)}</dd>
              <dt>人口区间</dt>
              <dd>{region.population.estimate_range.map((v: number) => v.toLocaleString()).join(" - ")}</dd>
              <dt>民心</dt>
              <dd>{runtime.support}</dd>
              <dt>动乱</dt>
              <dd>{runtime.unrest}</dd>
              <dt>军压</dt>
              <dd>{region.pressure}</dd>
              <dt>城防</dt>
              <dd>{runtime.fortification}</dd>
              <dt>粮储</dt>
              <dd>{region.grain.stock_glu.toLocaleString()} 粮秣</dd>
              <dt>月赋</dt>
              <dd>{region.tax.cp_per_30_days.toLocaleString()} 财政点</dd>
            </dl>
            <Meter value={runtime.unrest} danger />
            <p>{cn(region.status)}</p>
          </>
        )}
      </aside>
    </div>
  );
}

export function FinanceView({ snap }: { snap: Snapshot }) {
  const f = snap.management.finance;
  return (
    <section>
      <SectionHead eyebrow="度支与粮运" title="户部总账" extra={<Wheat size={18} />} />
      <div className="finance-summary">
        <Metric label="可用现银" value={f.cash} unit="财政点" />
        <Metric label="中央粮储" value={f.grain} unit="粮秣点" />
        <Metric label="月入" value={f.monthly_income} />
        <Metric label="月支" value={f.monthly_expenses} />
        <Metric label="粮食月入" value={f.monthly_grain} />
      </div>
      <div className="data-table finance-table">
        <header>
          <span>账户</span>
          <span>类别</span>
          <span>余额</span>
          <span>依据</span>
        </header>
        {snap.catalog.initial_finance.accounts.map((account: any) => (
          <div key={account.id}>
            <span><b>{account.name}</b></span>
            <span>{cn(account.kind)}</span>
            <span>{account.balance.toLocaleString()}</span>
            <span><Evidence value={snap.catalog.initial_finance.evidence_status} /></span>
          </div>
        ))}
      </div>
    </section>
  );
}

export function ArmyCommandView({
  snap,
  onMove,
  onDirective,
}: {
  snap: Snapshot;
  onMove: (army: string, destination: string) => void;
  onDirective: (draft: any) => void;
}) {
  const activeAct = Number(snap.state.act_id?.replace("act", "")) || 1;
  const routes: Record<string, string[]> = {
    changan: ["tongguan", "mawei"], mawei: ["changan", "jiannan"],
    tongguan: ["changan", "lingbao"], lingbao: ["tongguan", "shanjun"],
    shanjun: ["lingbao", "luoyang"], luoyang: ["shanjun", "hedong", "suiyang"],
    hedong: ["luoyang", "fanyang", "shuofang"], fanyang: ["hedong", "changshan"],
    changshan: ["fanyang", "pingyuan"], pingyuan: ["changshan", "suiyang"],
    suiyang: ["pingyuan", "luoyang", "yangzhou"], yangzhou: ["suiyang"],
    shuofang: ["hedong", "hexi"], hexi: ["shuofang", "longyou"],
    longyou: ["hexi", "jiannan"], jiannan: ["longyou", "mawei"],
  };
  const available = snap.catalog.armies.filter((item: any) => item.act_from <= activeAct && item.power.startsWith("tang"));
  const [selected, setSelected] = React.useState(available[0]?.id || "");
  const army = snap.catalog.armies.find((item: any) => item.id === selected);
  const field = snap.strategy.armies?.[selected];
  const live = snap.management.armies[selected];
  const region = field?.region || live?.region || army?.region || "";
  const [destinationChoice, setDestinationChoice] = React.useState(routes[region]?.[0] || "");
  React.useEffect(() => setDestinationChoice(routes[region]?.[0] || ""), [region]);
  const regionName = snap.catalog.regions.find((item: any) => item.id === region)?.name || region;
  const issue = Object.entries(snap.management.issues).sort((a: any, b: any) => b[1].tension - a[1].tension)[0]?.[0];
  const command = (id: string) => {
    if (!army) return;
    if (id === "move") {
      if (destinationChoice) onMove(army.id, destinationChoice);
      return;
    }
    const draft =
      id === "fortify"
        ? { kind: "fortify", target: region, amount: 10, subject: army.name + "驻防" }
        : id === "investigate"
        ? { kind: "investigate", target: issue, amount: 10, subject: army.name + "斥候" }
        : id === "train"
        ? { kind: "supply", target: army.id, amount: 8, subject: army.name + "整训" }
        : { kind: id, target: army.id, amount: 10, subject: army.name };
    onDirective(draft);
  };
  return (
    <section className="army-command">
      <SectionHead eyebrow="天下兵马" title="军令台" extra={<span>军令先入队，回合推进时统一执行</span>} />
      <div className="army-command-grid">
        <div className="army-map">
          <CampaignMap data={snap.catalog} management={snap.management} strategy={snap.strategy} selected={region} />
          <div className="army-tabs">
            {available.map((item: any) => (
              <button className={selected === item.id ? "active" : ""} key={item.id} onClick={() => setSelected(item.id)}>
                {item.name}
              </button>
            ))}
          </div>
        </div>
        <article className="army-dossier">
          <span>兵部鱼袋 · 在册军伍</span>
          <h2>{army?.name || "未选军队"}</h2>
          <p>{snap.catalog.characters.find((item: any) => item.id === army?.commander)?.name || "统帅待定"} 统领 · 驻 {regionName}</p>
          <label className="army-route-select">
            预定调往
            <select value={destinationChoice} onChange={(e) => setDestinationChoice(e.target.value)} disabled={!routes[region]?.length}>
              <option value="">选择相邻目的地</option>
              {(routes[region] || []).map((id) => (
                <option value={id} key={id}>{snap.catalog.regions.find((item: any) => item.id === id)?.name || id}</option>
              ))}
            </select>
          </label>
          <dl>
            <dt>在队</dt>
            <dd>{Number(field?.strength ?? live?.strength ?? 0).toLocaleString()}</dd>
            <dt>可战</dt>
            <dd>{Number(live?.fit_strength ?? army?.fit_strength ?? 0).toLocaleString()}</dd>
            <dt>补给</dt>
            <dd>{field?.supply ?? live?.supply ?? 0}</dd>
            <dt>士气</dt>
            <dd>{field?.morale ?? live?.morale ?? 0}</dd>
          </dl>
          <Meter value={field?.supply ?? live?.supply ?? 0} />
          <small>调动只登记目的地，不会立即改变驻地；推进回合时由行军规则和推演模型共同写入战报。</small>
        </article>
        <div className="army-action-grid">
          {armyActions.map((actionMeta) => {
            const { Icon, ...action } = actionMeta;
            return (
              <button
                key={action.id}
                onClick={() => command(action.id)}
                disabled={!army || (action.id === "move" && !destinationChoice)}
                style={{ backgroundImage: "linear-gradient(#1517132b,#151713e8),url('/assets/ui/army-actions/" + action.asset + ".webp')" }}
              >
                <Icon className="army-action-icon" aria-hidden="true" />
                <b>{action.label}</b>
                <span>{action.note}</span>
              </button>
            );
          })}
        </div>
      </div>
      {(snap.strategy.pending_movements?.length || snap.management.directives.length) > 0 && (
        <div className="army-queue">
          <b>本回合待执行</b>
          {(snap.strategy.pending_movements || []).map((item: any) => (
            <span key={item.army_id}>
              调动 · {snap.catalog.armies.find((army: any) => army.id === item.army_id)?.name || item.army_id} →{" "}
              {snap.catalog.regions.find((region: any) => region.id === item.destination)?.name || item.destination}
            </span>
          ))}
          {snap.management.directives.map((item) => (
            <span key={item.id}>
              {item.subject?.includes("整训") ? "整训整备" : directiveMeta[item.kind]?.label || item.kind} · {item.subject || item.target} · 投入 {item.amount}
            </span>
          ))}
        </div>
      )}
      {snap.strategy.battle_log?.length > 0 && (
        <div className="battle-log">
          <h3>近期战报</h3>
          {snap.strategy.battle_log.slice(0, 5).map((item: string, index: number) => (
            <p key={index}>{item}</p>
          ))}
        </div>
      )}
    </section>
  );
}

export function ReportCenter({ snap }: { snap: Snapshot }) {
  const [filter, setFilter] = React.useState("全部");
  const reports = [
    ...snap.agent_runs.map((item: any) => ({
      kind: item.kind.includes("推演") ? "推演" : item.kind.includes("奏对") ? "奏对" : "模型",
      title: item.kind,
      body: item.detail || item.model + " · " + (item.succeeded ? "已完成" : "已回退"),
      meta: item.created_at,
    })),
    ...snap.strategy.battle_log.slice(0, 8).map((item: string) => ({
      kind: "军报",
      title: "战场动态",
      body: item,
      meta: "本回合",
    })),
    ...(snap.progress.active_event
      ? [{ kind: "事件", title: snap.progress.active_event.title, body: snap.progress.active_event.summary, meta: "待裁决" }]
      : []),
  ];
  const visible = filter === "全部" ? reports : reports.filter((item) => item.kind === filter);
  return (
    <section className="report-center">
      <SectionHead eyebrow="中书门下 · 兵部" title="奏报中心" extra={<span>{reports.length} 条记录</span>} />
      <div className="report-filters">
        {["全部", "军报", "推演", "奏对", "事件"].map((item) => (
          <button key={item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)}>
            {item}
          </button>
        ))}
      </div>
      <div className="report-layout">
        <div className="report-feed">
          {visible.length ? (
            visible.map((item: any, index: number) => (
              <article className={"report-card report-" + item.kind} key={item.title + "-" + index}>
                <header>
                  <b>{item.title}</b>
                  <small>{item.kind} · {item.meta}</small>
                </header>
                <p>{item.body}</p>
              </article>
            ))
          ) : (
            <p className="empty-note">此类奏报尚未形成。</p>
          )}
        </div>
        <aside className="report-side">
          <SectionHead eyebrow="当前事件" title="待裁事项" />
          {snap.progress.active_event ? (
            <article className="current-matter">
              <b>{snap.progress.active_event.title}</b>
              <p>{snap.progress.active_event.summary}</p>
              <small>推进回合前可召对、拟诏，裁决会与军令统一结算。</small>
            </article>
          ) : (
            <p className="empty-note">当前没有待裁事件。</p>
          )}
          <SectionHead eyebrow="持续事项" title="跨章债务" />
          {snap.catalog.ongoing_issues.slice(0, 5).map((issue: any) => (
            <div className="report-debt" key={issue.id}>
              <b>{issue.name}</b>
              <strong>{issue.pressure}</strong>
              <Meter value={issue.pressure} danger />
            </div>
          ))}
        </aside>
      </div>
    </section>
  );
}

export function MemorialsView({ snap }: { snap: Snapshot }) {
  const actIndex = Math.max(0, Number(snap.state.act_id?.replace("act", "")) - 1);
  const act = snap.catalog.acts[actIndex] || snap.catalog.acts[0];
  return (
    <section>
      <SectionHead eyebrow="中书门下" title={`${act.name} · 事件候选`} extra={<Clock3 size={18} />} />
      <div className="memorial-list">
        {act.event_candidates.map((event: any, index: number) => (
          <article key={event.id}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <div>
              <b>{event.name}</b>
              <p>满足对应军情、人物与时间条件后触发</p>
              <small>{event.historical_window === "counterfactual" ? "反事实分支" : event.historical_window.replace("..", "至")}</small>
            </div>
            <Evidence value={event.evidence_status} />
          </article>
        ))}
      </div>
      <SectionHead eyebrow="持续事项" title="跨章债务" />
      {snap.catalog.ongoing_issues.map((issue: any) => (
        <div className="long-issue" key={issue.id}>
          <div>
            <b>{issue.name}</b>
            <p>{issue.public_summary}</p>
          </div>
          <strong>{issue.pressure}</strong>
          <Evidence value={issue.evidence_status} />
        </div>
      ))}
    </section>
  );
}

export function PolicyFocusViewRich({ snap, onSelect }: { snap: Snapshot; onSelect: (id: string) => void }) {
  const completed = new Set<string>(snap.progress.completed_policies || []);
  const active = snap.progress.active_policy;
  return (
    <section className="policy-view">
      <SectionHead eyebrow="经国远图" title="国策树" extra={<span>每回合至多推进一项</span>} />
      <p className="policy-intro">选择一个可用节点。国策在本回合推进时完成，并写入帝国修正；前置节点和资源不足会阻止施行。</p>
      <div className="policy-tree">
        {focusBranches.map((branch) => (
          <div className={"policy-branch " + branch.tone} key={branch.name}>
            <h3>{branch.name}</h3>
            <div>
              {branch.nodes.map((node: any) => {
                const done = completed.has(node.id);
                const available = !done && !active && node.requires.every((req: string) => completed.has(req));
                return (
                  <button
                    className={"policy-node " + (done ? "unlocked" : available ? "available" : "locked")}
                    key={node.id}
                    disabled={!available}
                    title={policyEffects[node.id]}
                    onClick={() => onSelect(node.id)}
                  >
                    <span>{done ? <CheckCircle2 /> : available ? <CirclePlay /> : <LockKeyhole />}</span>
                    <b>{node.title}</b>
                    <small>{done ? "帝国修正已生效" : policyEffects[node.id] || "需要前置国策"}</small>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function highlightKeywords(text: string): string {
  return text.replace(
    /(升|降|加|减|增|削|调|拨|遣|募|裁|赈|征|修|筑|改|复|夺|授|罢|封|迁|徙|发)([^，。！？\n]{0,20}(?:[\d一二三四五六七八九十百千万]+[万两石骑人户亩]?)?)/g,
    (_, verb, rest) => `<mark class="kw-${verb.charCodeAt(0)}">${verb}${rest}</mark>`,
  );
}

function renderReportBody(text: string) {
  const parts = text.split(/(&lt;&lt;&lt;SECTION:(.+?)&gt;&gt;&gt;)/g);
  if (parts.length <= 1) {
    // Fallback: split by Chinese section headers
    return text.split("\n").map((line, i) => {
      if (!line.trim()) return <br key={i} />;
      const hMatch = line.match(/^[一二三四五六七八九十]+[、．.]\s*(.+)/);
      if (hMatch) return <h4 key={i}>{highlightKeywords(line)}</h4>;
      if (/^【.+】$/.test(line.trim())) return <h4 key={i} className="report-subhead">{highlightKeywords(line)}</h4>;
      return <p key={i} dangerouslySetInnerHTML={{ __html: highlightKeywords(line) }} />;
    });
  }
  // Structured sections
  const elements: React.ReactNode[] = [];
  for (let i = 0; i < parts.length; i++) {
    if (parts[i].startsWith("<<<SECTION:")) {
      elements.push(<h4 key={`h-${i}`} className="report-section-header">{parts[i + 1]}</h4>);
      i++;
    } else if (parts[i].trim()) {
      parts[i].split("\n").forEach((line, j) => {
        if (!line.trim()) elements.push(<br key={`${i}-${j}`} />);
        else elements.push(<p key={`${i}-${j}`} dangerouslySetInnerHTML={{ __html: highlightKeywords(line) }} />);
      });
    }
  }
  return elements;
}

export function HistoryView({ state, resolution }: { state: any; resolution: any }) {
  const isReportStreaming = resolution && resolution.report !== undefined && !resolution.report_end;
  return (
    <section className="history-view">
      <SectionHead eyebrow="起居注与露布" title="本局史册" extra={<BookOpen size={18} />} />

      {resolution && (
        <div className="resolution-report">
          <div className="report-scroll-header">
            <span className="scroll-seal">唐</span>
            <div>
              <small>第 {resolution.turn} 回合</small>
              <h3>{resolution.reportTitle || "月末奏章"}</h3>
              {resolution.campaign && <span className="scroll-subtitle">{resolution.campaign.title || resolution.campaign.ending || ""}</span>}
            </div>
          </div>

          {resolution.report ? (
            <div className={`report-card ${isReportStreaming ? "streaming" : ""}`}>
              <div className="report-body">{renderReportBody(resolution.report)}</div>
              {isReportStreaming && <span className="typing-cursor">▌</span>}
            </div>
          ) : resolution.gazette ? (
            <div className="gazette-card">
              <b>邸报</b>
              <div className="report-body">{renderReportBody(resolution.gazette)}</div>
            </div>
          ) : resolution.narration ? (
            <div className="gazette-card">
              <b>史官纪事</b>
              <p>{resolution.narration}</p>
            </div>
          ) : null}

          {resolution.reports && resolution.reports.length > 0 && (
            <div className="directive-outcomes">
              <b>诏令执行</b>
              {resolution.reports.map((report: any) => (
                <div key={report.directive_id} className={report.accepted ? "accepted" : "rejected"}>
                  <b>{report.accepted ? "✓" : "✗"} {report.headline}</b>
                  <span>{report.effects?.join("；") || report.reason}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="chronicle">
        <b>史册编年</b>
        {state.history.map((item: string, index: number) => (
          <article key={`${item}-${index}`}>
            <span>{String(state.history.length - index).padStart(3, "0")}</span>
            <p>{item}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ObjectivePanel({ snap }: { snap: Snapshot }) {
  const objectives = [
    ["三回合内稳住潼关军令", snap.progress.total_turn <= 3 ? "进行中" : "期限已过"],
    ["查明前线军报真伪", snap.management.issues?.tongguan_intelligence?.progress >= 50 ? "已推进" : "待推进"],
    ["维持中央粮储不少于五百", snap.management.finance.grain >= 500 ? "达成" : "告急"],
  ];
  return (
    <aside className="objective-panel">
      <header>
        <span>短期任务</span>
        <b>天宝十五载 · 潼关危局</b>
      </header>
      {objectives.map(([title, status], index) => (
        <article key={title}>
          <em>0{index + 1}</em>
          <div>
            <b>{title}</b>
            <small>{status}</small>
          </div>
        </article>
      ))}
    </aside>
  );
}

function SituationPanel({ snap }: { snap: Snapshot }) {
  const situations = snap.progress.situations || [];
  const modifiers = snap.progress.modifiers || [];
  return (
    <section className="situation-panel">
      <header>
        <div>
          <span>国势仪表</span>
          <h2>局势进度</h2>
        </div>
        <small>每回合由推演模型综合判断</small>
      </header>
      <div className="situation-list">
        {situations.map((item: any) => (
          <article key={item.id}>
            <div className="situation-title">
              <b>{item.title}</b>
              <span className={item.trend === "恶化" ? "down" : item.trend === "向好" ? "up" : ""}>
                {item.trend === "向好" ? <TrendingUp size={13} /> : item.trend === "恶化" ? <TrendingDown size={13} /> : <Clock3 size={13} />}{" "}
                {item.status}
              </span>
            </div>
            <p>{item.summary}</p>
            <div className="situation-meter">
              <i
                className={item.status === "已崩坏" ? "failed" : item.status === "已完成" ? "complete" : ""}
                style={{ width: String(item.progress) + "%" }}
              />
            </div>
            <small>{item.progress}/100 · {item.last_reason}</small>
          </article>
        ))}
      </div>
      {modifiers.length > 0 && (
        <div className="modifier-strip">
          <b>帝国修正</b>
          {modifiers.slice(-5).map((item: any) => (
            <span key={item.id + "-" + item.applied_turn} title={item.description}>{item.name}</span>
          ))}
        </div>
      )}
    </section>
  );
}
