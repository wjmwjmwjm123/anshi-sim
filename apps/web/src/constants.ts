import {
  Binoculars, Castle, Dumbbell, Landmark, ListChecks, MapPinned,
  MessageSquareText, PackageOpen, Route, ScrollText, SearchCheck, Shield, ShieldCheck,
  Swords, Undo2, UserRoundPlus, Users,
} from "lucide-react";
import type {
  ArmyAction, DirectiveMeta, NavItem, OrderMeta, Tab,
} from "./types";

export const nav: NavItem[] = [
  { id: "court" as Tab, label: "朝堂", Icon: Users },
  { id: "overview" as Tab, label: "军情", Icon: Shield },
  { id: "map" as Tab, label: "天下", Icon: MapPinned },
  { id: "army" as Tab, label: "诸军", Icon: Swords },
  { id: "memorials" as Tab, label: "奏报", Icon: ScrollText },
  { id: "policy" as Tab, label: "国策", Icon: Landmark },
  { id: "history" as Tab, label: "史册", Icon: MessageSquareText },
];

export const orders: OrderMeta[] = [
  { id: "hold", title: "闭关固守", note: "耗时一旬", gain: "稳军心、固营垒", risk: "皇威受损", Icon: ShieldCheck },
  { id: "verify", title: "三路复核", note: "耗时三日", gain: "提高情报置信", risk: "贻误战机", Icon: SearchCheck },
  { id: "reconcile", title: "召对释疑", note: "耗时一日", gain: "统一军令", risk: "朝争加剧", Icon: MessageSquareText },
  { id: "constrain", title: "更易监军", note: "耗时三日", gain: "压低谣报", risk: "将帅不满", Icon: ListChecks },
  { id: "prepare_retreat", title: "整备退路", note: "耗时五日", gain: "防止溃退级联", risk: "士气波动", Icon: Undo2 },
  { id: "sally", title: "奉诏出击", note: "立即决战", gain: "结算灵宝战局", risk: "准备不足则大溃", Icon: Swords },
];

export const directiveMeta: DirectiveMeta = {
  relief: { label: "开仓赈济", domain: "regions" },
  tax: { label: "加征赋税", domain: "regions" },
  supply: { label: "转运军粮", domain: "armies" },
  mobilize: { label: "征发兵员", domain: "armies" },
  fortify: { label: "修筑城防", domain: "regions" },
  investigate: { label: "查明情形", domain: "issues" },
  appoint: { label: "授官任职", domain: "characters" },
  mediate: { label: "调停争端", domain: "issues" },
};

export const evidenceLabel: Record<string, string> = {
  documented: "史实锚定",
  disputed: "史料争议",
  estimate: "制作估算",
  design_estimate: "虚构设计",
};

export const attributeLabel: Record<string, string> = {
  military: "统兵",
  administration: "治政",
  politics: "权术",
  diplomacy: "交涉",
  loyalty: "忠诚",
  integrity: "操守",
};

export const powerLabel: Record<string, string> = {
  tang_xuanzong: "玄宗朝廷",
  tang_suzong: "肃宗朝廷",
  yan_an: "安氏燕廷",
  yan_shi: "史氏燕廷",
  uighur: "回纥",
  tibet: "吐蕃",
  contested: "争夺中",
};

export const statusLabel: Record<string, string> = {
  capital_under_threat: "京师告急",
  fortified_front: "坚城前线",
  ambush_corridor: "伏击狭道",
  yan_forward_base: "燕军前进基地",
  yan_capital: "燕廷都城",
  yan_home_base: "燕军根本",
  split_control: "分裂控制",
  loyal_military_base: "忠唐军镇",
  western_garrison: "西陲军镇",
  tibetan_frontier: "吐蕃边境",
  fallback_capital_candidate: "行在候选",
  imperial_escape_route: "皇驾西行路线",
  occupied_resistance: "敌后抵抗",
  loyal_resistance: "忠唐抵抗",
  jianghuai_gateway: "江淮门户",
  canal_revenue_hub: "漕运财赋枢纽",
  defending: "据守",
  active_campaign: "出征中",
  ambush_prepared: "设伏待敌",
  strategic_reserve: "战略预备",
  hebei_campaign: "河北作战",
  asset: "资产",
  grain_asset: "粮食资产",
  receivable: "待解收入",
  liability: "支出承诺",
  restricted_asset: "专用储备",
  corroborated: "已互证",
  contradicted: "已反证",
  unverified: "待核",
};

export const cn = (value: string) => statusLabel[value] || powerLabel[value] || value;

export const armyActions: ArmyAction[] = [
  { id: "move", label: "调动", note: "沿相邻驿道转移驻地", asset: "movement", Icon: Route },
  { id: "supply", label: "补给", note: "调拨粮秣，维持远征", asset: "supply", Icon: PackageOpen },
  { id: "train", label: "整训", note: "整顿军纪，恢复可战兵", asset: "tiger-tally", Icon: Dumbbell },
  { id: "mobilize", label: "征募", note: "补充兵员，增加军费", asset: "recruitment", Icon: UserRoundPlus },
  { id: "fortify", label: "驻防", note: "加固当前州郡城防", asset: "fortress", Icon: Castle },
  { id: "investigate", label: "侦察", note: "核验当前最急军情", asset: "scouting", Icon: Binoculars },
];

export const eventArt: Record<string, string> = {
  shi_assassination: "shi_siming_assassination",
  shi_siming_assassination: "shi_siming_assassination",
  heshuo_surrender: "heshuo_surrender",
  heshuo_settlement: "heshuo_surrender",
  tibet_threat: "tibet_changan_threat",
  tibet_changan_threat: "tibet_changan_threat",
};

export const modelRoles: Record<string, { name: string; note: string }> = {
  chat: { name: "人物议政", note: "人物扮演、朝堂争论、密诏与远奏" },
  simulation: { name: "回合推演", note: "长上下文、多因素分析与结算叙事" },
  utility: { name: "文书与记忆", note: "诏书润色、奏折生成、摘要与长期记忆" },
};

export const policyEffects: Record<string, string> = {
  unify_command: "军令局势 +10；朝堂冲突下降",
  repair_post_roads: "军令局势 +6；传令更稳定",
  restrain_eunuchs: "军令局势 +8；皇威承压后回升",
  reinforce_tongguan: "城防 +8；驻军士气 +3",
  shuofang_recruit: "朔方增兵约 6,000；消耗现银",
  contact_resistance: "河朔人心 +12；民心略升",
  divide_yan: "河朔人心 +16；叛军内部分裂",
  secure_grain_route: "月粮 +15；月入 +8",
  relieve_guanzhong: "粮储 -80；各地民心上升",
};

export const focusBranches = [
  { name: "中枢整饬", tone: "civil", nodes: [
    { id: "unify_command", title: "整饬军令体系", requires: [] },
    { id: "repair_post_roads", title: "重建驿传", requires: [] },
    { id: "restrain_eunuchs", title: "裁抑近习干政", requires: ["unify_command"] },
  ]},
  { name: "军镇经略", tone: "war", nodes: [
    { id: "reinforce_tongguan", title: "加强潼关防务", requires: [] },
    { id: "shuofang_recruit", title: "朔方整军募骑", requires: ["reinforce_tongguan"] },
  ]},
  { name: "河朔联络", tone: "frontier", nodes: [
    { id: "contact_resistance", title: "联络河北义军", requires: [] },
    { id: "divide_yan", title: "离间燕廷诸将", requires: ["contact_resistance"] },
  ]},
  { name: "财赋民生", tone: "people", nodes: [
    { id: "secure_grain_route", title: "保全江淮漕运", requires: [] },
    { id: "relieve_guanzhong", title: "关中军民赈济", requires: ["secure_grain_route"] },
  ]},
];
