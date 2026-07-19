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
  three_edicts: "three_edicts",
  lingbao_decision: "lingbao_battle",
  lingbao_battle: "lingbao_battle",
  changan_escape: "changan_escape",
  mawei_mutiny: "mawei_mutiny",
  lingwu_accession: "lingwu_accession",
  yan_succession: "an_lushan_succession",
  uighur_treaty: "uighur_treaty",
  suiyang_siege: "suiyang_siege",
  recapture_capitals: "recapture_capitals",
  luoyang_aftermath: "second_luoyang_crisis",
  xiangzhou_command: "xiangzhou_command",
  shi_surrender: "shi_siming_surrender",
  shi_rebellion: "second_luoyang_crisis",
  heyange_defense: "hold_tongguan",
  eunuch_command: "three_edicts",
  luoyang_second_fall: "second_luoyang_crisis",
  shuofang_rivalry: "xiangzhou_command",
  western_withdrawal: "tibet_changan_threat",
  shi_assassination: "shi_siming_assassination",
  shi_siming_assassination: "shi_siming_assassination",
  final_luoyang: "second_luoyang_crisis",
  heshuo_surrender: "heshuo_surrender",
  heshuo_settlement: "heshuo_surrender",
  tibet_threat: "tibet_changan_threat",
  tibet_changan_threat: "tibet_changan_threat",
  uighur_payment: "uighur_treaty",
  postwar_court: "lingwu_accession",
};

// Act ending generated art mapping
export const actEndingArt: Record<string, string> = {
  act1: "/assets/generated/endings/act1.webp",
  act2: "/assets/generated/endings/act2.webp",
  act3: "/assets/generated/endings/act3.webp",
  act4: "/assets/generated/endings/act4.webp",
  act5: "/assets/generated/endings/act5.webp",
};

export const modelRoles: Record<string, { name: string; note: string }> = {
  chat: { name: "人物议政", note: "人物扮演、朝堂争论、密诏与远奏" },
  simulation: { name: "回合推演", note: "长上下文、多因素分析与结算叙事" },
  utility: { name: "文书与记忆", note: "诏书润色、奏折生成、摘要与长期记忆" },
};

export const policyEffects: Record<string, string> = {
  unify_command: "军令局势 +10；朝堂冲突下降",
  repair_post_roads: "军令局势 +6；传令更稳定",
  restrain_eunuchs: "军令局势 +8；皇威 +5",
  rebuild_censorate: "朝堂冲突 -15；皇威 +8",
  court_reform: "中枢效率 +20；月入 +5",
  reinforce_tongguan: "潼关城防 +8；驻军士气 +3",
  shuofang_recruit: "朔方增兵约 6,000；消耗现银 120",
  hexi_defense: "西陲空虚 -12；吐蕃压力缓解",
  naval_jianghuai: "漕运安全 +15；月入 +4",
  imperial_guard: "皇威 +12；禁军建立拱卫长安",
  contact_resistance: "河朔人心 +12；民心 +3",
  divide_yan: "河朔人心 +16；叛军内部疑惧",
  recruit_hebei: "河北民心 +8；可征发新兵 3,000",
  heshuo_negotiate: "藩镇自主 +15；但军费下降",
  rebellion_pardon: "河朔人心 +20；部分叛军归降",
  secure_grain_route: "月粮 +15；月入 +8",
  relieve_guanzhong: "粮储 -80；关中民心 +15",
  land_survey: "月入 +12；士绅阻力 +10",
  salt_tax_reform: "月入 +18；盐商不满上升",
  trade_silk_road: "月入 +25；西陲商道恢复",
};

export const focusBranches = [
  { name: "中枢整饬", tone: "civil", nodes: [
    { id: "unify_command", title: "整饬军令体系", requires: [], desc: "统一各镇节度使军令，杜绝监军越权指挥" },
    { id: "repair_post_roads", title: "重建驿传", requires: [], desc: "修复潼关至长安驿道，确保军情三日内抵京" },
    { id: "restrain_eunuchs", title: "裁抑近习干政", requires: ["unify_command"], desc: "限制宦官监军权，还军令于将帅" },
    { id: "rebuild_censorate", title: "重整御史台", requires: ["restrain_eunuchs"], desc: "恢复御史弹劾之权，制衡中书门下" },
    { id: "court_reform", title: "三省合议改制", requires: ["rebuild_censorate"], desc: "确立政事堂合议制度，提高中枢决策效率" },
  ]},
  { name: "军镇经略", tone: "war", nodes: [
    { id: "reinforce_tongguan", title: "加强潼关防务", requires: [], desc: "增筑潼关城防，补足守军粮械" },
    { id: "shuofang_recruit", title: "朔方整军募骑", requires: ["reinforce_tongguan"], desc: "于朔方镇征募骑兵五千，组建机动援军" },
    { id: "hexi_defense", title: "河西走廊防务", requires: ["shuofang_recruit"], desc: "巩固河西诸军镇，防止吐蕃趁虚而入" },
    { id: "naval_jianghuai", title: "江淮水师操练", requires: [], desc: "建设江淮水师，保漕运并策应沿江战事" },
    { id: "imperial_guard", title: "重建禁军六军", requires: ["shuofang_recruit", "naval_jianghuai"], desc: "招募关中精锐组建天子亲军，拱卫京畿" },
  ]},
  { name: "河朔联络", tone: "frontier", nodes: [
    { id: "contact_resistance", title: "联络河北义军", requires: [], desc: "派密使联络常山颜真卿、平原颜杲卿等忠唐势力" },
    { id: "divide_yan", title: "离间燕廷诸将", requires: ["contact_resistance"], desc: "诱降安禄山麾下汉将，分裂叛军内部" },
    { id: "recruit_hebei", title: "河北招抚流亡", requires: ["contact_resistance"], desc: "招纳河北逃难百姓充军，重建地方保甲" },
    { id: "heshuo_negotiate", title: "藩镇羁縻之策", requires: ["divide_yan"], desc: "与反正藩镇谈判世袭、赋税与驻军条件" },
    { id: "rebellion_pardon", title: "颁诏赦降纳顺", requires: ["heshuo_negotiate"], desc: "明诏赦免归降叛将，保留部曲但有条件听调" },
  ]},
  { name: "财赋民生", tone: "people", nodes: [
    { id: "secure_grain_route", title: "保全江淮漕运", requires: [], desc: "确保运河粮道畅通，关中月粮不低于百石" },
    { id: "relieve_guanzhong", title: "关中军民赈济", requires: ["secure_grain_route"], desc: "开仓赈济关中流民，抑制动乱蔓延" },
    { id: "land_survey", title: "清丈关陇田亩", requires: ["relieve_guanzhong"], desc: "清查隐田逃赋，扩大税基以充国库" },
    { id: "salt_tax_reform", title: "盐铁专卖整顿", requires: [], desc: "整顿盐铁衙门，打击私盐增加岁入" },
    { id: "trade_silk_road", title: "重开丝路商道", requires: ["hexi_defense", "salt_tax_reform"], desc: "确保陇右商道安全，恢复西域贸易税收" },
  ]},
];
