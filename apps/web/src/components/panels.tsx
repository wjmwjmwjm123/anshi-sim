import React from "react";
import {
  Clock3, FilePenLine, MessageSquareText, Settings, Trash2, X,
} from "lucide-react";
import type { DirectiveKind, Snapshot } from "../types";
import { api } from "../api";
import { Portrait, SectionHead } from "./shared";
import { directiveMeta, eventArt, modelRoles, orders } from "../constants";

export function DirectiveDock({
  snap,
  onAdd,
  onRemove,
  onResolve,
  busy,
}: {
  snap: Snapshot;
  onAdd: (draft: any) => void;
  onRemove: (id: number) => void;
  onResolve: () => void;
  busy: boolean;
}) {
  const [kind, setKind] = React.useState<DirectiveKind>("relief");
  const [target, setTarget] = React.useState("");
  const [amount, setAmount] = React.useState(10);
  const [subject, setSubject] = React.useState("");
  const domain = directiveMeta[kind].domain;
  const options = Object.entries((snap.management as any)[domain] || {});
  const actualTarget = target || options[0]?.[0] || "";
  React.useEffect(() => setTarget(""), [kind]);
  return (
    <section className="directive-dock">
      <div className="directive-form">
        <div className="dock-title">
          <FilePenLine size={18} />
          <span>拟诏</span>
        </div>
        <select value={kind} onChange={(e) => setKind(e.target.value as DirectiveKind)} aria-label="诏令类型">
          {Object.entries(directiveMeta).map(([id, meta]) => (
            <option key={id} value={id}>{meta.label}</option>
          ))}
        </select>
        <select value={actualTarget} onChange={(e) => setTarget(e.target.value)} aria-label="诏令对象">
          {options.map(([id, value]: any) => (
            <option key={id} value={id}>{value.name || value.title}</option>
          ))}
        </select>
        <input
          type="number"
          min="1"
          max="100"
          value={amount}
          onChange={(e) => setAmount(Number(e.target.value))}
          aria-label="投入规模"
        />
        {kind === "appoint" ? (
          <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="授予官职" />
        ) : ["investigate", "mediate"].includes(kind) ? (
          <select value={subject} onChange={(e) => setSubject(e.target.value)} aria-label="承办人">
            <option value="">不指定承办</option>
            {Object.entries(snap.management.characters)
              .filter(([, c]: [string, any]) => c.status === "active")
              .map(([id, c]: [string, any]) => (
                <option key={id} value={id}>{c.name}</option>
              ))}
          </select>
        ) : null}
        <button onClick={() => onAdd({ kind, target: actualTarget, amount, subject })} disabled={!actualTarget || busy}>加入诏令</button>
      </div>
      {snap.management.directives.length > 0 && (
        <div className="directive-queue">
          <span>待颁 {snap.management.directives.length} 道</span>
          {snap.management.directives.map((item) => (
            <div key={item.id}>
              <b>{directiveMeta[item.kind].label}</b>
              <small>
                {((snap.management as any)[directiveMeta[item.kind].domain]?.[item.target]?.name ||
                  (snap.management as any)[directiveMeta[item.kind].domain]?.[item.target]?.title ||
                  item.target)}{" "}
                · {item.amount}
              </small>
              <button onClick={() => onRemove(item.id)} title="删除诏令" aria-label="删除诏令">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
      <button className="resolve-btn" onClick={onResolve} disabled={busy}>
        {busy ? "正在结算…" : snap.management.directives.length > 0 ? `颁诏并推进 · ${snap.management.directives.length} 道` : "推进一回合"}
      </button>
    </section>
  );
}

export function AudienceDrawer({
  character,
  office,
  conversation,
  onClose,
  onSecret,
}: {
  character: any;
  office?: string;
  conversation?: any;
  onClose: () => void;
  onSecret: (data: any) => Promise<any>;
}) {
  const [topic, setTopic] = React.useState("当前最紧要之事是什么？");
  const [reply, setReply] = React.useState<any>(null);
  const [busy, setBusy] = React.useState(false);
  const [scene, setScene] = React.useState(character.audience_status === "remote_only" ? "远奏" : "朝堂");
  const ask = async () => {
    setBusy(true);
    const response = await api.audience.ask({ character_id: character.id, topic, scene: scene as any });
    setReply(response);
    setBusy(false);
  };
  const labels: Record<string, string> = {
    military: "统兵", administration: "治政", politics: "权术", diplomacy: "交涉", loyalty: "忠诚", integrity: "操守",
  };
  const rel = conversation?.relationships?.[character.id];
  const chatHistory: any[] = conversation?.chats?.[character.id] || [];
  return (
    <div className={`audience-stage scene-${scene}`} role="dialog" aria-modal="true">
      <button className="drawer-scrim" onClick={onClose} aria-label="关闭" />
      <section className="audience-paper">
        <button className="drawer-close" onClick={onClose} aria-label="关闭">
          <X size={18} />
        </button>
        <aside className="audience-figure">
          <Portrait character={character} large />
          <h2>{character.name}</h2>
          <small>{office || character.identity}</small>
          <p>{character.public_stance}</p>
          {rel && (
            <div className="relationship-mini">
              <div className="rel-row"><span>信任</span><b className={rel.trust < 35 ? "low" : rel.trust > 65 ? "high" : ""}>{rel.trust}</b></div>
              <div className="rel-row"><span>恩宠</span><b className={rel.favor < -10 ? "low" : rel.favor > 30 ? "high" : ""}>{rel.favor >= 0 ? "+" : ""}{rel.favor}</b></div>
              <div className="rel-row"><span>畏惧</span><b className={rel.fear > 60 ? "low" : ""}>{rel.fear}</b></div>
              {rel.promises?.length > 0 && (
                <div className="promises-tag" title={rel.promises.join("；")}>
                  诺言 {rel.promises.length}
                </div>
              )}
            </div>
          )}
        </aside>
        <main className="audience-conversation">
          <header>
            <b>{scene}奏对</b>
            <div className="scene-switch">
              {["朝堂", "密诏", "远奏"].map((value) => (
                <button key={value} className={scene === value ? "active" : ""} onClick={() => setScene(value)}>{value}</button>
              ))}
            </div>
          </header>
          <div className="dialogue-flow">
            <div className="player-line">{topic}</div>
            {reply && (
              <div className="minister-line">
                <Portrait character={character} />
                <p>
                  {reply.accepted ? reply.reply : reply.detail}
                  <small>{reply.model_used ? "联网人物推演" : "规则与中文模板"}</small>
                </p>
              </div>
            )}
            {chatHistory.length > 0 && (
              <details className="chat-recall">
                <summary>此前奏对 ({chatHistory.length / 2} 轮)</summary>
                {chatHistory.map((m: any, i: number) => (
                  <div key={i} className={m.role === "皇帝" ? "recall-emperor" : "recall-minister"}>
                    <small>T{m.turn} · {m.scene}</small>
                    <span>{m.text.length > 80 ? m.text.slice(0, 80) + "…" : m.text}</span>
                  </div>
                ))}
              </details>
            )}
          </div>
          <div className="audience-input">
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="在此问策、下令或试探其心意……"
            />
            <button className="ask-btn" onClick={ask} disabled={busy}>
              <MessageSquareText size={16} />{busy ? "候奏中" : "发送"}
            </button>
            {scene === "密诏" && (
              <button
                className="secret-btn"
                onClick={async () => {
                  await onSecret({ character_id: character.id, text: topic, purpose: "密查" });
                  setReply({ accepted: true, reply: "密诏已封缄交付，将跨回合记录进展。", model_used: false });
                }}
              >
                封缄密诏
              </button>
            )}
          </div>
          <div className="attribute-grid">
            {Object.entries(character.attributes).map(([k, v]: [string, any]) => (
              <span key={k}>{labels[k] || "属性"}<b>{v}</b></span>
            ))}
          </div>
        </main>
      </section>
    </div>
  );
}

export function CouncilModal({ snap, onClose }: { snap: Snapshot; onClose: () => void }) {
  const people = snap.catalog.characters
    .filter(
      (c: any) =>
        snap.management.characters[c.id]?.status === "active" &&
        !["enemy_only", "future_enemy", "player_character"].includes(c.audience_status),
    )
    .slice(0, 14);
  const [selected, setSelected] = React.useState<string[]>(people.slice(0, 3).map((c: any) => c.id));
  const [topic, setTopic] = React.useState("潼关应当固守，还是奉诏出击？");
  const [exchanges, setExchanges] = React.useState<any[]>([]);
  const [rounds, setRounds] = React.useState<any[]>([]);
  const [busy, setBusy] = React.useState(false);
  const [phase, setPhase] = React.useState<"setup" | "done" | "continue" | "emperor">("setup");
  const toggle = (id: string) =>
    setSelected((v) => (v.includes(id) ? v.filter((x) => x !== id) : v.length < 6 ? [...v, id] : v));

  const runRound = async (roundNo: number, prevMinutes: string, emperorRemark: string) => {
    setBusy(true);
    setPhase("done");
    setExchanges([]);
    const controller = new AbortController();
    try {
      await api.council.stream(
        { character_ids: selected, topic, round_no: roundNo, previous_minutes: prevMinutes, emperor_remark: emperorRemark },
        (d: any) => {
          if (d.error) return;
          if (d.done) return;
          if (d.type === "speech_start") {
            setExchanges((prev) => [...prev, { name: d.name, reply: "", streaming: true }]);
          } else if (d.type === "speech_delta") {
            setExchanges((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.streaming) {
                return [...prev.slice(0, -1), { ...last, reply: last.reply + d.delta }];
              }
              return prev;
            });
          } else if (d.type === "speech_end") {
            setExchanges((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.streaming && last.name === d.name) {
                return [...prev.slice(0, -1), { ...last, reply: d.reply || last.reply, streaming: false }];
              }
              return [...prev, { name: d.name, reply: d.reply, streaming: false }];
            });
          } else if (d.type === "minutes") {
            setRounds((prev) => [...prev, { round: d.round, minutes: d.text }]);
          } else if (d.type === "emperor_options") {
            setPhase(d.is_final ? "emperor" : "continue");
          }
        },
        controller.signal,
      );
    } finally {
      setBusy(false);
    }
  };

  const discuss = () => runRound(1, "", "");
  const nextRound = (remark: string) => {
    const lastMin = rounds.length ? rounds[rounds.length - 1].minutes : "";
    runRound(rounds.length + 1, lastMin, remark);
  };

  if (phase === "setup") {
    return (
      <div className="council-stage">
        <button className="drawer-scrim" onClick={onClose} />
        <section className="council-hall">
          <button className="drawer-close" onClick={onClose}>
            <X size={18} />
          </button>
          <header>
            <span>紫宸殿集议</span>
            <h2>召集群臣，共议军国</h2>
            <p>选择二至六人入殿。后发言者会听见前臣意见，并依人设与利益作出回应。</p>
          </header>
          <div className="council-seats">
            {people.map((person: any) => (
              <button
                key={person.id}
                className={selected.includes(person.id) ? "selected" : ""}
                onClick={() => toggle(person.id)}
              >
                <Portrait character={person} />
                <b>{person.name}</b>
                <small>{snap.management.characters[person.id]?.office || person.identity}</small>
              </button>
            ))}
          </div>
          <div className="council-topic">
            <textarea value={topic} onChange={(e) => setTopic(e.target.value)} />
            <button onClick={discuss} disabled={busy || selected.length < 2}>
              {busy ? "群臣议论中" : "开议"}
            </button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="council-stage">
      <button className="drawer-scrim" onClick={onClose} />
      <section className="council-hall">
        <button className="drawer-close" onClick={onClose}>
          <X size={18} />
        </button>
        <header>
          <span>紫宸殿集议</span>
          <h2>{topic}</h2>
        </header>
        <div className="council-transcript">
          {rounds.map((r) => (
            <div key={r.round} className="council-minutes">
              <b>{r.round === "final" ? "最终纪要" : `第${r.round}轮纪要`}</b>
              <p>{r.minutes}</p>
            </div>
          ))}
          {exchanges.map((item: any, index: number) => (
            <article key={`${item.name}-${index}`} className={item.streaming ? "streaming" : ""}>
              <Portrait character={people.find((p: any) => p.name === item.name)} />
              <div>
                <b>{item.name}</b>
                <p>
                  {item.reply}
                  {item.streaming && <span className="typing-cursor">▌</span>}
                </p>
              </div>
            </article>
          ))}
          {busy && <p className="council-busy">群臣议论中…</p>}
          {(phase === "continue" || phase === "emperor") && (
            <div className="emperor-panel">
              <b>{phase === "emperor" ? "陛下圣裁" : "第一轮已毕"}</b>
              <div className="emperor-actions">
                {phase === "emperor" && (
                  <button
                    onClick={() => {
                      const remark = window.prompt("陛下谕旨：");
                      if (remark !== null) nextRound(remark);
                    }}
                  >
                    👑 朕有话说
                  </button>
                )}
                {phase === "emperor" && <button onClick={() => setPhase("done")}>📜 查看总结</button>}
                <button onClick={onClose}>⚖️ 就此裁决</button>
                <button onClick={() => nextRound("")}>{phase === "emperor" ? "💬 继续廷议" : "⚔️ 进入第二轮"}</button>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export function DecreeReview({
  decree,
  onConfirm,
  onClose,
}: {
  decree: any;
  onConfirm: (id: number) => void;
  onClose: () => void;
}) {
  return (
    <div className="drawer-layer" role="dialog" aria-modal="true">
      <button className="drawer-scrim" onClick={onClose} aria-label="关闭" />
      <aside className="audience-drawer decree-review">
        <button className="drawer-close" onClick={onClose}>
          <X size={18} />
        </button>
        <FilePenLine size={28} />
        <h2>中书核议</h2>
        <small>{decree.model_used ? "文书模型已拟写圣旨" : "文书模型未配置，暂保留原始诏意"}</small>
        <blockquote>{decree.rendered_text || decree.text}</blockquote>
        {decree.decision && (
          <div className="decree-decision">
            <b>并入御前裁决</b>
            <span>《{decree.decision.title}》：{decree.decision.choice}</span>
          </div>
        )}
        <h3>模型拆出的朝堂行动</h3>
        {decree.candidates.map((item: any, index: number) => (
          <div className="candidate-command" key={index}>
            <b>{directiveMeta[item.kind as DirectiveKind]?.label || "立项核议"}</b>
            <span>投入 {item.amount}</span>
            <small>{item.reason}</small>
          </div>
        ))}
        {decree.candidates.length ? (
          <button className="ask-btn" onClick={() => onConfirm(decree.id)}>列入本回合行动</button>
        ) : (
          <p className="decree-empty">文书模型未返回可执行行动；可直接颁行圣旨与已暂存裁决，或修改诏意后重拟。</p>
        )}
        <p className="compact-note">行动、御前裁决与诏书将在“颁诏”时统一结算。</p>
      </aside>
    </div>
  );
}

export function EventDecision({
  event,
  onChoose,
  onClose,
  busy,
}: {
  event: any;
  onChoose: (choice: string) => void;
  onClose: () => void;
  busy: boolean;
}) {
  const art = eventArt[event.id];
  return (
    <section className="event-scroll" aria-label="御前裁断">
      <button className="drawer-close" onClick={onClose} aria-label="暂不裁断">
        <X size={18} />
      </button>
      {art && <img className="event-art" src={`/assets/events/${art}.webp`} alt="" />}
      <div className="scroll-ribbon">御前裁断</div>
      <div className="event-copy">
        <span>第 {event.turn} 回合 · 军国奏牍</span>
        <h2>{event.title}</h2>
        <p>{event.summary}</p>
        {busy && (
          <p className="decision-busy">
            <Clock3 aria-hidden="true" />正在暂存裁决，请稍候…
          </p>
        )}
        <div>
          {event.choices.map((choice: string) => (
            <button key={choice} onClick={() => onChoose(choice)} disabled={busy}>
              暂存：{choice}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

export function EdictComposer({
  onClose,
  onSubmit,
  busy,
  decision,
  issued,
}: {
  onClose: () => void;
  onSubmit: (text: string) => void;
  busy: boolean;
  decision?: any;
  issued: any[];
}) {
  const [parts, setParts] = React.useState<Record<string, string>>({ 军务: "", 内政: "", 外事: "", 其他: "" });
  const total = Object.values(parts).reduce((sum, text) => sum + text.length, 0);
  const submit = () => {
    const text = Object.entries(parts)
      .filter(([, value]) => value.trim())
      .map(([kind, value]) => `【${kind}】\n${value.trim()}`)
      .join("\n\n");
    if (text) onSubmit(text);
  };
  return (
    <div className="edict-stage" role="dialog" aria-modal="true">
      <button className="drawer-scrim" onClick={onClose} />
      <section className="edict-paper">
        <button className="drawer-close" onClick={onClose}>
          <X size={18} />
        </button>
        <header>
          <span>奉天承运皇帝诏曰</span>
          <h2>御笔拟诏</h2>
          <small>中书将用文书模型生成圣旨，并将行动拆为受约束事项</small>
        </header>
        {decision && (
          <div className="edict-decision">本回合御前裁决：<b>《{decision.title}》</b> · {decision.choice}</div>
        )}
        <div className="edict-columns">
          {Object.keys(parts).map((kind) => (
            <label key={kind}>
              <b>{kind[0]}</b>
              <span>{kind}</span>
              <textarea
                value={parts[kind]}
                onChange={(e) => setParts({ ...parts, [kind]: e.target.value })}
                placeholder="写下你的旨意……"
                maxLength={2000}
              />
              <small>{parts[kind].length}/2000</small>
            </label>
          ))}
        </div>
        <footer>
          <span>本轮诏书 · 共 {total} 字</span>
          <button onClick={submit} disabled={!total || busy}>{busy ? "中书核议中" : "送中书核议"}</button>
        </footer>
        {issued.length > 0 && (
          <section className="edict-register">
            <b>本局已颁圣旨</b>
            {issued.slice(0, 3).map((item: any) => (
              <p key={item.id}>第 {item.promulgated_turn || item.turn} 回合 · {item.rendered_text || item.text}</p>
            ))}
          </section>
        )}
      </section>
    </div>
  );
}

export function MultiModelDrawer({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: () => void;
}) {
  const [configs, setConfigs] = React.useState<any>({});
  const [active, setActive] = React.useState("chat");
  const [form, setForm] = React.useState({ api_key: "", base_url: "", model: "" });
  const [note, setNote] = React.useState("");
  React.useEffect(() => {
    api.modelConfig.get().then((data) => setConfigs(data.roles || {}));
  }, []);
  React.useEffect(() => {
    const cfg = configs[active] || {};
    setForm({ api_key: "", base_url: cfg.base_url || "", model: cfg.model || "" });
  }, [active, configs]);
  const save = async () => {
    const r = await api.modelConfig.update({ ...form, role: active });
    setNote(r.detail || "");
    setConfigs((current: any) => ({
      ...current,
      [active]: { ...current[active], configured: !!r, base_url: r.base_url || form.base_url, model: r.model || form.model },
    }));
    setForm({ ...form, api_key: "" });
    onSaved();
  };
  return (
    <div className="drawer-layer model-center" role="dialog">
      <button className="drawer-scrim" onClick={onClose} />
      <section className="model-console">
        <button className="drawer-close" onClick={onClose}>
          <X size={18} />
        </button>
        <header>
          <span>模型分工</span>
          <h2>三司推演配置</h2>
          <p>每项可使用不同供应商、接口和模型；密钥仅保存在当前后端进程。</p>
        </header>
        <nav>
          {Object.entries(modelRoles).map(([id, item]) => (
            <button className={active === id ? "active" : ""} key={id} onClick={() => setActive(id)}>
              <b>{item.name}</b>
              <small>{item.note}</small>
              <em>{configs[id]?.configured ? configs[id].model || "已配置" : "使用通用回退"}</em>
            </button>
          ))}
        </nav>
        <main>
          <label>接口地址<input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} /></label>
          <label>模型名称<input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} /></label>
          <label>API 密钥
            <input type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} placeholder="留空则沿用当前密钥" />
          </label>
          <button className="ask-btn" onClick={save}>应用此职责配置</button>
          {note && <blockquote>{note}</blockquote>}
        </main>
      </section>
    </div>
  );
}

export function ModelDrawer({
  snap,
  onClose,
  onSaved,
}: {
  snap: Snapshot;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [key, setKey] = React.useState("");
  const [base, setBase] = React.useState("");
  const [model, setModel] = React.useState("");
  const [note, setNote] = React.useState("");
  React.useEffect(() => {
    api.modelConfig.get().then((data) => {
      setBase(data.base_url || "");
      setModel(data.model || "");
    });
  }, []);
  const save = async () => {
    const r = await api.modelConfig.update({ api_key: key, base_url: base, model });
    setKey("");
    setNote(r.detail || "");
    onSaved();
  };
  return (
    <div className="drawer-layer" role="dialog" aria-modal="true">
      <button className="drawer-scrim" onClick={onClose} aria-label="关闭" />
      <aside className="audience-drawer model-drawer">
        <button className="drawer-close" onClick={onClose} aria-label="关闭">
          <X size={18} />
        </button>
        <Settings size={28} />
        <h2>联网模型</h2>
        <p>人物奏对与每回合史官推演使用 OpenAI 兼容接口。规则数值始终由本地确定性结算。</p>
        <label>API 密钥
          <input type="password" value={key} onChange={(e) => setKey(e.target.value)} placeholder={snap.runtime["联网模型"]} />
        </label>
        <label>接口地址<input value={base} onChange={(e) => setBase(e.target.value)} /></label>
        <label>模型名称<input value={model} onChange={(e) => setModel(e.target.value)} /></label>
        <button className="ask-btn" onClick={save}>应用当前进程</button>
        {note && <blockquote>{note}</blockquote>}
      </aside>
    </div>
  );
}
