from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class CampaignEvent:
    id: str
    title: str
    act_id: str
    turn: int
    summary: str
    choices: list[str]
    resolved: bool = False


@dataclass
class CampaignProgress:
    act: int = 1
    act_turn: int = 1
    total_turn: int = 1
    year: int = 756
    month: int = 6
    active_event: CampaignEvent | None = None
    pending_event_choice: dict[str, str] | None = None
    completed_events: list[str] = field(default_factory=list)
    secret_edicts: list[dict] = field(default_factory=list)
    obligations: dict[str, int] = field(default_factory=lambda: {"回纥债务": 0, "藩镇自主": 20, "西陲空虚": 15, "战争疲敝": 28})
    ending: str = ""


ACT_NAMES = {1: "潼关危局", 2: "皇统裂变", 3: "收复两京", 4: "胜而未定", 5: "平乱之后"}
ACT_LENGTHS = {1: 2, 2: 6, 3: 12, 4: 36, 5: 24}

EVENTS = {
    1: [
        (1, "three_edicts", "一日三使催战", "朝廷与潼关行营的军令已相互冲突。", ["支持固守", "催军出战", "复核敌情"]),
        (2, "lingbao_decision", "灵宝决断", "出关与否将决定关中门户。", ["继续固守", "有备出关", "立即决战"]),
    ],
    2: [
        (1, "changan_escape", "玄宗西幸", "潼关局势动摇，长安百官与宫眷开始西行。", ["保全皇驾", "留守长安", "太子分兵北上"]),
        (3, "mawei_mutiny", "马嵬兵变", "禁军饥疲，将士要求诛除杨氏。", ["诛杨国忠", "强行护持", "高力士调停"]),
        (5, "lingwu_accession", "灵武即位", "太子与朔方将士形成新的权力中心。", ["承认新帝", "维持玄宗诏命", "暂立双中心"]),
    ],
    3: [
        (1, "yan_succession", "燕廷弑主", "安禄山病重，燕廷继承危机爆发。", ["乘乱反攻", "联络河北降将", "稳固江淮"]),
        (3, "uighur_treaty", "回纥借兵", "回纥愿出骑兵，但索取厚赏与战利品。", ["重金结盟", "限制战利品", "拒绝借兵"]),
        (5, "suiyang_siege", "睢阳告急", "江淮门户粮尽援绝。", ["全力救援", "命其死守", "撤民弃城"]),
        (7, "recapture_capitals", "两京反攻", "唐军获得反攻长安、洛阳的窗口。", ["先长安后洛阳", "两路并进", "继续整军"]),
        (10, "luoyang_aftermath", "洛阳善后", "收复地区的军纪、粮秣与官署都亟待重建。", ["严整军纪", "优先筹粮", "安抚旧官"]),
    ],
    4: [
        (1, "xiangzhou_command", "相州九节度", "诸军会师却无统一主帅。", ["郭子仪总领", "宦官监军", "分镇自战"]),
        (4, "shi_surrender", "史思明请降", "史思明愿降唐，要求保留部曲与地盘。", ["受降羁縻", "调离河北", "拒降进讨"]),
        (6, "shi_rebellion", "史思明复叛", "河北安抚失衡，燕军重新集结。", ["集中主力", "坚守河阳", "招抚诸将"]),
        (12, "heyange_defense", "河阳守御", "史思明攻势直逼河阳，东京屏障动摇。", ["李光弼坚守", "增援河阳", "退保陕州"]),
        (18, "eunuch_command", "内廷监军", "宦官与节度使争夺战场指挥权。", ["收回监军权", "维持制衡", "增设观军容使"]),
        (24, "luoyang_second_fall", "洛阳再陷", "燕军卷土重来，东京守备面临崩解。", ["固守宫城", "撤民坚壁", "外围决战"]),
        (30, "shuofang_rivalry", "朔方将帅嫌隙", "功臣、内廷与新进将领围绕军权互相猜忌。", ["郭子仪复职", "分割军权", "内廷总领"]),
        (35, "western_withdrawal", "西军内调", "河西陇右精锐持续东调，吐蕃压力显著上升。", ["停止内调", "继续东援", "招募本地守军"]),
    ],
    5: [
        (1, "shi_assassination", "史思明被弑", "燕廷再次陷入父子相残。", ["分化燕将", "立即北伐", "保全关中"]),
        (3, "final_luoyang", "洛阳终局", "唐回纥联军准备最后进攻。", ["借兵决战", "唐军独进", "围困待降"]),
        (5, "heshuo_surrender", "河朔请降", "叛军诸将愿奉唐正朔，但要求世守本镇。", ["授节度留任", "拆分军镇", "彻底讨平"]),
        (7, "tibet_threat", "吐蕃乘虚", "西陲兵力内调，吐蕃已逼近关中。", ["回师西陲", "以和市缓兵", "先平河朔"]),
        (12, "uighur_payment", "盟约索偿", "回纥使者催索财帛、婚盟与战利品承诺。", ["如约偿付", "分期拖延", "拒绝旧约"]),
        (18, "heshuo_settlement", "河朔置帅", "降将归镇后，朝廷必须决定军镇是否世袭。", ["承认世袭", "定期轮换", "拆镇置州"]),
        (23, "postwar_court", "平乱朝议", "战争将终，功臣、宦官、藩镇与百姓都在索取代价。", ["优先休养", "强化中央", "酬赏功臣"]),
    ],
}


def initial_progress() -> CampaignProgress:
    progress = CampaignProgress()
    progress.active_event = _event_for(progress)
    return progress


def advance(progress: CampaignProgress, choice: str = "") -> dict:
    if progress.ending:
        return {"advanced": False, "ending": progress.ending, "progress": asdict(progress)}
    resolved = None
    if progress.active_event:
        if not choice:
            return {"advanced": False, "requires_choice": True, "event": asdict(progress.active_event), "progress": asdict(progress)}
        resolved = _resolve_choice(progress, progress.active_event, choice)
        progress.active_event.resolved = True
        progress.completed_events.append(progress.active_event.id)
        progress.active_event = None

    progress.total_turn += 1
    progress.act_turn += 1
    _advance_calendar(progress)
    if progress.act_turn > ACT_LENGTHS[progress.act]:
        if progress.act == 5:
            progress.ending = _ending(progress)
        else:
            progress.act += 1
            progress.act_turn = 1
    event = _event_for(progress)
    if event:
        progress.active_event = event
    _drift(progress)
    secret_updates = _advance_secret_edicts(progress)
    return {"advanced": True, "resolved": resolved, "event": asdict(event) if event else None, "secret_updates": secret_updates, "progress": asdict(progress)}


def add_secret_edict(progress: CampaignProgress, recipient: str, text: str, purpose: str) -> dict:
    edict = {"id": len(progress.secret_edicts) + 1, "recipient": recipient, "text": text.strip(), "purpose": purpose, "issued_turn": progress.total_turn, "status": "进行中", "progress": 0, "result": ""}
    progress.secret_edicts.append(edict)
    return edict


def _advance_secret_edicts(progress: CampaignProgress) -> list[str]:
    updates: list[str] = []
    for edict in progress.secret_edicts:
        if edict["status"] != "进行中":
            continue
        edict["progress"] = min(100, int(edict.get("progress", 0)) + 35)
        if edict["progress"] >= 100:
            edict["status"] = "已办结"
            edict["result"] = f"{edict['recipient']}已就“{edict['purpose']}”递交密奏，内容可供下一次裁断参考。"
            updates.append(edict["result"])
        else:
            updates.append(f"{edict['recipient']}承办密诏“{edict['purpose']}”，进度{edict['progress']}%。")
    return updates


def _event_for(progress: CampaignProgress) -> CampaignEvent | None:
    for turn, event_id, title, summary, choices in EVENTS[progress.act]:
        if turn == progress.act_turn and event_id not in progress.completed_events:
            return CampaignEvent(event_id, title, f"act{progress.act}", progress.total_turn, summary, choices)
    return None


def _resolve_choice(progress: CampaignProgress, event: CampaignEvent, choice: str) -> dict:
    if choice not in event.choices:
        raise ValueError("所选裁断不在当前事件选项中")
    impacts: list[str] = []
    if "回纥" in event.title or "借兵" in choice:
        progress.obligations["回纥债务"] += 25
        impacts.append("回纥债务上升")
    if any(word in choice for word in ("留任", "羁縻", "分镇")):
        progress.obligations["藩镇自主"] += 18
        impacts.append("藩镇自主上升")
    if any(word in choice for word in ("西陲", "和市")):
        progress.obligations["西陲空虚"] -= 12
        impacts.append("西陲压力下降")
    if any(word in choice for word in ("决战", "进讨", "北伐", "并进")):
        progress.obligations["战争疲敝"] += 10
        impacts.append("战争疲敝上升")
    return {"event_id": event.id, "title": event.title, "choice": choice, "impacts": impacts}


def _advance_calendar(progress: CampaignProgress) -> None:
    if progress.act == 1 and progress.act_turn == 2:
        return
    progress.month += 1
    if progress.month > 12:
        progress.month = 1
        progress.year += 1


def _drift(progress: CampaignProgress) -> None:
    progress.obligations["战争疲敝"] = min(100, progress.obligations["战争疲敝"] + 2)
    progress.obligations["西陲空虚"] = min(100, progress.obligations["西陲空虚"] + (2 if progress.act >= 3 else 0))
    for key in progress.obligations:
        progress.obligations[key] = max(0, min(100, progress.obligations[key]))


def _ending(progress: CampaignProgress) -> str:
    debt = progress.obligations
    if debt["藩镇自主"] >= 75:
        return "乱平而镇强：燕军覆亡，河朔却成为朝廷难以直接控制的军镇。"
    if debt["西陲空虚"] >= 70:
        return "东乱既平，西陲失守：唐廷收复两京，却无力阻止吐蕃东进。"
    if debt["回纥债务"] >= 60:
        return "借兵复国：两京重归唐室，巨额盟约与战利品之债长期侵蚀朝廷。"
    return "艰难中兴：唐廷平定主乱，并保留了重整中央与边防的余地。"
