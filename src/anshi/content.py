from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EvidenceStatus = Literal["documented", "estimate", "design", "disputed"]


class Manifest(BaseModel):
    scenario_id: str
    title: str
    schema_version: int = Field(ge=1)
    content_version: str
    start_date: str
    calendar: str


class Region(BaseModel):
    id: str
    name: str
    controller_id: str
    terrain: list[str]
    morale: int = Field(ge=0, le=100)
    unrest: int = Field(ge=0, le=100)
    evidence_status: EvidenceStatus


class Route(BaseModel):
    id: str
    from_id: str
    to_id: str
    base_days: float = Field(gt=0)
    capacity_glu_day: int = Field(gt=0)
    ambush_risk: int = Field(ge=0, le=100)
    bidirectional: bool = True


class Army(BaseModel):
    id: str
    name: str
    power_id: str
    commander_id: str
    region_id: str
    paper_strength: int = Field(gt=0)
    present_strength: int = Field(gt=0)
    fit_strength: int = Field(gt=0)
    available_from: str
    evidence_status: EvidenceStatus

    @model_validator(mode="after")
    def strength_order(self) -> "Army":
        if not self.fit_strength <= self.present_strength <= self.paper_strength:
            raise ValueError("army strength must satisfy fit <= present <= paper")
        return self


class Character(BaseModel):
    id: str
    name: str
    role: str
    power_id: str
    region_id: str
    available_from: str
    evidence_status: EvidenceStatus


class Act(BaseModel):
    id: str
    title: str
    date_range: str
    objective: str
    entry_condition: str
    exit_condition: str


class Scenario(BaseModel):
    manifest: Manifest
    world: dict
    regions: list[Region]
    routes: list[Route]
    armies: list[Army]
    characters: list[Character]
    acts: list[Act]

    @model_validator(mode="after")
    def references_are_valid(self) -> "Scenario":
        _unique("region", [x.id for x in self.regions])
        _unique("route", [x.id for x in self.routes])
        _unique("army", [x.id for x in self.armies])
        _unique("character", [x.id for x in self.characters])
        _unique("act", [x.id for x in self.acts])
        regions = {x.id for x in self.regions}
        characters = {x.id for x in self.characters}
        for route in self.routes:
            if route.from_id not in regions or route.to_id not in regions:
                raise ValueError(f"route {route.id} references an unknown region")
        for army in self.armies:
            if army.region_id not in regions or army.commander_id not in characters:
                raise ValueError(f"army {army.id} has an invalid region or commander")
            if army.available_from > self.manifest.start_date:
                raise ValueError(f"future army {army.id} cannot appear in the opening snapshot")
        for character in self.characters:
            if character.region_id not in regions:
                raise ValueError(f"character {character.id} references an unknown region")
        _assert_connected(regions, self.routes)
        return self


def load_scenario(path: str | Path) -> Scenario:
    root = Path(path)
    read = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    return Scenario(
        manifest=read("manifest.json"),
        world=read("world.json"),
        regions=read("regions.json"),
        routes=read("routes.json"),
        armies=read("armies.json"),
        characters=read("characters.json"),
        acts=read("acts.json"),
    )


def _unique(kind: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {kind} id")


def _assert_connected(region_ids: set[str], routes: list[Route]) -> None:
    graph = {region_id: set() for region_id in region_ids}
    for route in routes:
        graph[route.from_id].add(route.to_id)
        if route.bidirectional:
            graph[route.to_id].add(route.from_id)
    seen = set()
    queue = deque([next(iter(region_ids))])
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(graph[node] - seen)
    if seen != region_ids:
        raise ValueError(f"scenario map is disconnected: {sorted(region_ids - seen)}")

