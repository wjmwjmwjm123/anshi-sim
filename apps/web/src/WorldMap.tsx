import React from "react";
import "./maps.css";
import { cn } from "./constants";

type WorldRegion = {
  id: string;
  name: string;
  map: { x: number; y: number };
  controller: string;
  pressure: number;
  status: string;
  support?: number;
  unrest?: number;
};

type RegionRuntime = {
  support: number;
  unrest: number;
  fortification: number;
  tax_rate?: number;
};

type ArmyOnMap = {
  id: string;
  name: string;
  power: string;
  region: string;
  strength: number;
  supply: number;
  morale: number;
  objective?: string;
};

type SiegeOnMap = {
  region: string;
  attacker: string;
  defender: string;
  progress: number;
  status: string;
};

type MovementOnMap = {
  army_id: string;
  destination: string;
};

type WorldMapProps = {
  data: { regions: WorldRegion[] };
  management: { regions: Record<string, RegionRuntime> };
  strategy?: {
    armies?: Record<string, ArmyOnMap>;
    sieges?: SiegeOnMap[];
    pending_movements?: MovementOnMap[];
    battle_log?: string[];
  };
  selected?: string;
  onSelect?: (id: string) => void;
};

type Allegiance = "tang" | "yan" | "contested";

interface Adjacency { [key: string]: string[] }

const ROUTES: Adjacency = {
  changan: ["tongguan", "mawei"], mawei: ["changan", "jiannan"],
  tongguan: ["changan", "lingbao"], lingbao: ["tongguan", "shanjun"],
  shanjun: ["lingbao", "luoyang"], luoyang: ["shanjun", "hedong", "suiyang"],
  hedong: ["luoyang", "fanyang", "shuofang"], fanyang: ["hedong", "changshan"],
  changshan: ["fanyang", "pingyuan"], pingyuan: ["changshan", "suiyang"],
  suiyang: ["pingyuan", "luoyang", "yangzhou"], yangzhou: ["suiyang"],
  shuofang: ["hedong", "hexi"], hexi: ["shuofang", "longyou"],
  longyou: ["hexi", "jiannan"], jiannan: ["longyou", "mawei"],
};

const labelOffsets: Record<string, [number, number]> = {
  changan: [-30, 18], tongguan: [-22, -20], lingbao: [4, 21],
  shanjun: [18, -19], luoyang: [31, 12], fanyang: [28, -18],
  hedong: [-30, -18], shuofang: [-28, -18], hexi: [-32, 5],
  longyou: [-35, 18], jiannan: [-28, 22], mawei: [-35, 35],
  changshan: [-32, -17], pingyuan: [31, 14], suiyang: [28, 24],
  yangzhou: [28, 18],
};

function allegiance(controller: string): Allegiance {
  if (controller.startsWith("yan")) return "yan";
  if (controller === "contested") return "contested";
  return "tang";
}

function armySide(power: string): Allegiance {
  if (power.startsWith("yan")) return "yan";
  if (power.startsWith("tang")) return "tang";
  return "contested";
}

function fmt(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  return String(n);
}

export default function WorldMap({ data, management, strategy, selected, onSelect }: WorldMapProps) {
  const [detailRegion, setDetailRegion] = React.useState<string | null>(null);
  const [selectedArmy, setSelectedArmy] = React.useState<string | null>(null);
  const [zoom, setZoom] = React.useState(1);
  const [pan, setPan] = React.useState({ x: 0, y: 0 });
  const [dragging, setDragging] = React.useState(false);
  const dragRef = React.useRef<{ sx: number; sy: number; px: number; py: number } | null>(null);
  const canvasRef = React.useRef<HTMLDivElement>(null);
  const zoomIn = () => setZoom((z) => Math.min(2, +(z + 0.25).toFixed(2)));
  const zoomOut = () => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)));
  const zoomReset = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  const onPointerDown = (e: React.PointerEvent) => {
    if (zoom <= 1) return;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    dragRef.current = { sx: e.clientX, sy: e.clientY, px: pan.x, py: pan.y };
    setDragging(true);
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (!dragRef.current) return;
    const dx = e.clientX - dragRef.current.sx;
    const dy = e.clientY - dragRef.current.sy;
    setPan({ x: dragRef.current.px + dx / zoom, y: dragRef.current.py + dy / zoom });
  };
  const onPointerUp = () => {
    dragRef.current = null;
    setDragging(false);
  };

  const counts = data.regions.reduce(
    (total, r) => ({ ...total, [allegiance(r.controller)]: total[allegiance(r.controller)] + 1 }),
    { tang: 0, yan: 0, contested: 0 } as Record<Allegiance, number>,
  );

  const armies = strategy?.armies ?? {};
  const sieges = strategy?.sieges ?? [];
  const pending = strategy?.pending_movements ?? [];
  const armiesByRegion: Record<string, ArmyOnMap[]> = {};
  Object.values(armies).forEach((a) => {
    (armiesByRegion[a.region] ??= []).push(a);
  });
  const siegesByRegion: Record<string, SiegeOnMap[]> = {};
  sieges.forEach((s) => {
    (siegesByRegion[s.region] ??= []).push(s);
  });

  const selectedArmyObj = selectedArmy ? armies[selectedArmy] : null;
  const routeTargets: string[] = selectedArmyObj
    ? ROUTES[selectedArmyObj.region] ?? []
    : [];

  const openDetail = detailRegion ? data.regions.find((r) => r.id === detailRegion) : null;
  const detailRuntime = openDetail ? management.regions[openDetail.id] : null;
  const detailArmies = openDetail ? armiesByRegion[openDetail.id] ?? [] : [];
  const detailSieges = openDetail ? siegesByRegion[openDetail.id] ?? [] : [];

  return (
    <div className="world-map">
      <header className="world-map-summary">
        <div><span>州镇舆图</span><b>{data.regions.length} 处军政地区</b></div>
        <dl>
          <div className="tang"><dt>唐辖</dt><dd>{counts.tang}</dd></div>
          <div className="yan"><dt>燕据</dt><dd>{counts.yan}</dd></div>
          <div className="contested"><dt>争夺</dt><dd>{counts.contested}</dd></div>
        </dl>
      </header>

      <div
        className={`world-map-canvas ${dragging ? "dragging" : ""}`}
        role="group"
        aria-label="安史之乱天下州镇控制图"
        ref={canvasRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        <div
          className="world-map-layer"
          style={{ transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`, transformOrigin: "center center" }}
        >
          <img src="/assets/backgrounds/tang-terrain.webp" alt="唐代天下地形底图" />
          <span className="world-map-shade" />

          {/* Region markers */}
          {data.regions.map((region) => {
          const runtime = management.regions[region.id];
          const [dx, dy] = labelOffsets[region.id] || [0, 0];
          const side = allegiance(region.controller);
          const regionArmies = armiesByRegion[region.id] ?? [];
          const regionSieges = siegesByRegion[region.id] ?? [];
          return (
            <button
              key={region.id}
              className={`world-region ${side} ${selected === region.id ? "selected" : ""} ${detailRegion === region.id ? "focused" : ""}`}
              style={{
                left: `${region.map.x}%`,
                top: `${region.map.y}%`,
                "--label-x": `${dx}px`,
                "--label-y": `${dy}px`,
              } as React.CSSProperties}
              onClick={() => {
                onSelect?.(region.id);
                setDetailRegion(detailRegion === region.id ? null : region.id);
                setSelectedArmy(null);
              }}
              aria-pressed={selected === region.id || detailRegion === region.id}
              title={`${region.name} · ${cn(region.controller)}`}
            >
              <i />
              <span>
                <b>{region.name}</b>
                <small>{cn(region.status)}</small>
                <em>
                  民心 {runtime?.support ?? region.support ?? "-"} · 动乱 {runtime?.unrest ?? region.unrest ?? "-"}
                  {regionArmies.length > 0 ? ` · ${regionArmies.length}军` : ""}
                  {regionSieges.length > 0 ? " · 围城" : ""}
                </em>
              </span>
              {/* Army count badge */}
              {regionArmies.length > 0 && (
                <b className="army-badge">{regionArmies.length}</b>
              )}
              {/* Siege flame */}
              {regionSieges.length > 0 && (
                <span className="siege-icon" title="围城中">🔥</span>
              )}
            </button>
          );
        })}

        {/* SVG overlay for routes */}
        <svg className="route-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
          {selectedArmyObj && routeTargets.map((targetId) => {
            const src = data.regions.find((r) => r.id === selectedArmyObj.region);
            const dst = data.regions.find((r) => r.id === targetId);
            if (!src || !dst) return null;
            return (
              <line
                key={`${selectedArmyObj.region}-${targetId}`}
                x1={src.map.x}
                y1={src.map.y}
                x2={dst.map.x}
                y2={dst.map.y}
                className="route-highlight"
              />
            );
          })}
        </svg>

        {/* Army tokens */}
        {Object.entries(armies).map(([id, army]) => {
          const region = data.regions.find((r) => r.id === army.region);
          if (!region) return null;
          const side = armySide(army.power);
          const offset = (Object.keys(armiesByRegion[army.region] ?? {}).indexOf(id)) * 18;
          return (
            <button
              key={id}
              className={`army-token ${side} ${selectedArmy === id ? "selected" : ""}`}
              style={{
                left: `calc(${region.map.x}% + ${offset}px)`,
                top: `calc(${region.map.y}% + 14px)`,
              }}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedArmy(selectedArmy === id ? null : id);
              }}
              title={`${army.name} · 兵力${fmt(army.strength)} · 士气${army.morale} · 补给${army.supply}`}
              aria-label={`${army.name} ${side}军`}
            >
              <i className={side === "tang" ? "icon-tang" : "icon-yan"} />
            </button>
          );
        })}

        {/* Army detail popup */}
        {selectedArmyObj && (
          <div className="army-popup">
            <header>
              <b>{selectedArmyObj.name}</b>
              <button onClick={() => setSelectedArmy(null)} aria-label="关闭">✕</button>
            </header>
            <dl>
              <div><dt>所属</dt><dd>{cn(selectedArmyObj.power)}</dd></div>
              <div><dt>驻地</dt><dd>{data.regions.find((r) => r.id === selectedArmyObj.region)?.name ?? selectedArmyObj.region}</dd></div>
              <div><dt>兵力</dt><dd>{fmt(selectedArmyObj.strength)}</dd></div>
              <div><dt>补给</dt><dd className={selectedArmyObj.supply < 40 ? "danger" : ""}>{selectedArmyObj.supply}</dd></div>
              <div><dt>士气</dt><dd className={selectedArmyObj.morale < 40 ? "danger" : ""}>{selectedArmyObj.morale}</dd></div>
              {selectedArmyObj.objective && <div><dt>军令</dt><dd>{selectedArmyObj.objective}</dd></div>}
            </dl>
            {routeTargets.length > 0 && (
              <p className="route-hint">可调往：{routeTargets.map((rid) => data.regions.find((r) => r.id === rid)?.name ?? rid).join(" · ")}</p>
            )}
            {pending.some((m) => m.army_id === selectedArmy) && (
              <small className="move-pending">⏳ 已排入本回合行军队列</small>
            )}
          </div>
        )}
        </div>{/* end world-map-layer */}

        <footer className="world-map-legend">
          <span className="tang"><i />唐廷辖区</span>
          <span className="yan"><i />燕军占据</span>
          <span className="contested"><i />反复争夺</span>
          <span className="army-legend"><i className="icon-tang" /> 唐军</span>
          <span className="army-legend"><i className="icon-yan" /> 燕军</span>
        </footer>

        {/* Zoom controls */}
        <div className="map-zoom-controls">
          <button onClick={zoomIn} title="放大" aria-label="放大">+</button>
          <button onClick={zoomReset} title="还原" aria-label="还原">复原</button>
          <button onClick={zoomOut} title="缩小" aria-label="缩小">−</button>
        </div>
      </div>

      {/* Region detail panel */}
      {openDetail && detailRuntime && (
        <div className="region-detail-panel">
          <header>
            <h3>{openDetail.name}</h3>
            <button onClick={() => setDetailRegion(null)} aria-label="关闭">✕</button>
          </header>
          <dl>
            <div><dt>控制方</dt><dd className={allegiance(openDetail.controller)}>{cn(openDetail.controller)}</dd></div>
            <div><dt>状态</dt><dd>{cn(openDetail.status)}</dd></div>
            <div><dt>民心</dt><dd className={detailRuntime.support < 40 ? "danger" : ""}>{detailRuntime.support}</dd></div>
            <div><dt>动乱</dt><dd className={detailRuntime.unrest > 60 ? "danger" : ""}>{detailRuntime.unrest}</dd></div>
            <div><dt>城防</dt><dd>{detailRuntime.fortification}</dd></div>
            {detailRuntime.tax_rate != null && <div><dt>税率</dt><dd>{detailRuntime.tax_rate}</dd></div>}
          </dl>

          {detailArmies.length > 0 && (
            <section>
              <h4>驻军 ({detailArmies.length})</h4>
              {detailArmies.map((a) => (
                <div key={a.id} className={`mini-army ${armySide(a.power)}`}>
                  <b>{a.name}</b>
                  <span>兵{fmt(a.strength)} · 士气{a.morale} · 补给{a.supply}</span>
                </div>
              ))}
            </section>
          )}

          {detailSieges.length > 0 && (
            <section>
              <h4>围城</h4>
              {detailSieges.map((s, i) => (
                <div key={i} className="siege-bar">
                  <b>{s.attacker} → {s.defender}</b>
                  <span>{s.status}</span>
                  <progress value={s.progress} max={100}>{s.progress}%</progress>
                </div>
              ))}
            </section>
          )}
        </div>
      )}
    </div>
  );
}
