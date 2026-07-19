import React from "react";
import type { Catalog, Management } from "../types";
import { cn, evidenceLabel } from "../constants";

export function Metric({ label, value, unit = "", hint = "" }: { label: string; value: number | string; unit?: string; hint?: string }) {
  return (
    <div className="metric" data-hint={hint || undefined}>
      <span>{label}</span>
      <strong>{typeof value === "number" ? value.toLocaleString() : value}</strong>
      {hint && <small>{hint}</small>}
    </div>
  );
}

export function Meter({ value, danger = false }: { value: number; danger?: boolean }) {
  return (
    <span className={`mini-meter ${danger ? "danger" : ""}`}>
      <i style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </span>
  );
}

export function Evidence({ value }: { value: string }) {
  return <span className={`evidence ${value}`}>{evidenceLabel[value] || value}</span>;
}

export function Portrait({ character, large = false }: { character: any; large?: boolean }) {
  const [failed, setFailed] = React.useState(false);
  return failed ? (
    <span className={large ? "large-seal" : "portrait-seal"}>{character.name.slice(-1)}</span>
  ) : (
    <img
      className={large ? "portrait-image large" : "portrait-image"}
      src={`/assets/portraits/${character.id}.webp`}
      alt={character.name}
      onError={() => setFailed(true)}
    />
  );
}

export function SectionHead({ eyebrow, title, extra }: { eyebrow: string; title: string; extra?: React.ReactNode }) {
  return (
    <div className="section-head">
      <div>
        <span>{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {extra}
    </div>
  );
}

export function CampaignMap({
  data,
  management,
  strategy,
  selected,
  onSelect,
}: {
  data: Catalog;
  management: Management;
  strategy?: any;
  selected?: string;
  onSelect?: (id: string) => void;
}) {
  const armies = Object.values(strategy?.armies || {}) as any[];
  return (
    <div className="terrain-map" role="img" aria-label="安史之乱天下形势图">
      <img src="/assets/backgrounds/tang-terrain.webp" alt="唐代天下地形底图" />
      <div className="map-wash tang" />
      <div className="map-wash yan" />
      {data.regions.map((region: any) => {
        const runtime = management.regions[region.id];
        const controller = region.controller.startsWith("yan") ? "yan" : region.controller === "contested" ? "contested" : "tang";
        return (
          <button
            key={region.id}
            className={`terrain-point ${controller} ${selected === region.id ? "selected" : ""}`}
            style={{ left: `${region.map.x}%`, top: `${region.map.y}%` }}
            onClick={() => onSelect?.(region.id)}
            title={`${region.name} · ${cn(region.controller)}`}
          >
            <i />
            <b>{region.name.split("·")[0]}</b>
            <small>民心 {runtime?.support ?? "-"} · 动乱 {runtime?.unrest ?? "-"}</small>
          </button>
        );
      })}
      {armies.map((army: any) => {
        const region = data.regions.find((item: any) => item.id === army.region);
        if (!region) return null;
        const hostile = String(army.power).startsWith("yan");
        return (
          <span
            className={`map-standard ${hostile ? "yan" : "tang"}`}
            key={army.id}
            style={{ left: `${region.map.x + 2}%`, top: `${region.map.y - 7}%` }}
            title={`${army.name} · ${Number(army.strength).toLocaleString()}人`}
          >
            {hostile ? "燕" : "唐"}
          </span>
        );
      })}
      <div className="terrain-legend">
        <span><i className="tang" />唐军控制</span>
        <span><i className="yan" />燕军控制</span>
        <span><i className="contested" />争夺地区</span>
      </div>
    </div>
  );
}
