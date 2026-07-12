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
};

type WorldMapProps = {
  data: { regions: WorldRegion[] };
  management: { regions: Record<string, RegionRuntime> };
  selected?: string;
  onSelect?: (id: string) => void;
};

const labelOffsets: Record<string, [number, number]> = {
  changan: [-30, 18],
  tongguan: [-22, -20],
  lingbao: [4, 21],
  shanjun: [18, -19],
  luoyang: [31, 12],
  fanyang: [28, -18],
  hedong: [-30, -18],
  shuofang: [-28, -18],
  hexi: [-32, 5],
  longyou: [-35, 18],
  jiannan: [-28, 22],
  mawei: [-35, 35],
  changshan: [-32, -17],
  pingyuan: [31, 14],
  suiyang: [28, 24],
  yangzhou: [28, 18],
};

function allegiance(controller: string) {
  if (controller.startsWith("yan")) return "yan";
  if (controller === "contested") return "contested";
  return "tang";
}

export default function WorldMap({ data, management, selected, onSelect }: WorldMapProps) {
  const counts = data.regions.reduce(
    (total, region) => ({ ...total, [allegiance(region.controller)]: total[allegiance(region.controller)] + 1 }),
    { tang: 0, yan: 0, contested: 0 },
  );

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

      <div className="world-map-canvas" role="group" aria-label="安史之乱天下州镇控制图">
        <img src="/assets/backgrounds/tang-terrain.webp" alt="唐代天下地形底图" />
        <span className="world-map-shade" />
        {data.regions.map(region => {
          const runtime = management.regions[region.id];
          const [dx, dy] = labelOffsets[region.id] || [0, 0];
          const side = allegiance(region.controller);
          return (
            <button
              key={region.id}
              className={`world-region ${side} ${selected === region.id ? "selected" : ""}`}
              style={{
                left: `${region.map.x}%`,
                top: `${region.map.y}%`,
                "--label-x": `${dx}px`,
                "--label-y": `${dy}px`,
              } as React.CSSProperties}
              onClick={() => onSelect?.(region.id)}
              aria-pressed={selected === region.id}
              title={`${region.name} · ${cn(region.controller)}`}
            >
              <i />
              <span>
                <b>{region.name}</b>
                <small>{cn(region.status)}</small>
                <em>民心 {runtime?.support ?? region.support ?? "-"} · 动乱 {runtime?.unrest ?? region.unrest ?? "-"}</em>
              </span>
            </button>
          );
        })}
        <footer className="world-map-legend">
          <span className="tang"><i />唐廷辖区</span>
          <span className="yan"><i />燕军占据</span>
          <span className="contested"><i />反复争夺</span>
        </footer>
      </div>
    </div>
  );
}
