"""AI 图像生成模块。调用豆包 Seedream API 生图。"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen


def _load_image_config() -> tuple[str, str, str]:
    api_key = os.environ.get("IMAGE_API_KEY", "").strip()
    base_url = os.environ.get("IMAGE_BASE_URL", "https://ark.cn-beijing.volces.com/api/plan/v3/images/generations").strip()
    model = os.environ.get("IMAGE_MODEL", "doubao-seedream-5.0-lite").strip()
    if not api_key:
        raise RuntimeError("IMAGE_API_KEY 未配置")
    return api_key, base_url, model


def generate_image(
    prompt: str,
    *,
    size: str = "2K",
    negative_prompt: str = "",
    seed: int = -1,
) -> dict | None:
    """提交生图任务，返回 API response dict 或 None。"""
    api_key, base_url, model = _load_image_config()
    body: dict = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json",
    }
    if negative_prompt:
        body["negative_prompt"] = negative_prompt
    if seed >= 0:
        body["seed"] = seed

    req = Request(
        base_url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result
    except Exception as e:
        print(f"  [生图失败] {e}")
        return None


def generate_and_save(prompt: str, output_path: str | Path, **kwargs) -> bool:
    """生成一张图并保存到指定路径。返回是否成功。"""
    result = generate_image(prompt, **kwargs)
    if not result:
        return False
    images = result.get("data") or []
    if not images:
        return False
    b64 = images[0].get("b64_json", "")
    if not b64:
        return False
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(b64))
    return True


# ── 批量生图任务 ──

POLICY_PROMPTS = {
    # 中枢整饬
    "unify_command": ("中国古代战争场景：唐朝将领在军帐中研究地图，统一军令体系，严肃氛围，古风水墨画风", "2K"),
    "repair_post_roads": ("中国古代驿道场景：唐朝驿卒骑马奔驰在修缮一新的驿道上，传递军情，古风插画", "2K"),
    "restrain_eunuchs": ("唐朝宫廷场景：皇帝在大殿中裁抑宦官近习干政，文官肃立两旁，庄严氛围，古风工笔画", "2K"),
    "rebuild_censorate": ("唐朝御史台场景：官员在整理弹劾奏章，整饬吏治，古风水墨画风", "2K"),
    "court_reform": ("唐朝朝堂全景：三省六部官员整齐排列，中枢改革气象，庄重典雅，古风插画", "2K"),
    # 军镇经略
    "reinforce_tongguan": ("潼关要塞全景：唐军在高大城墙上加固防御，旌旗飘扬，雄伟壮观，古风山水画风", "2K"),
    "shuofang_recruit": ("朔方军营：唐朝骑兵在校场上操练，战马奔腾，军容壮盛，古风插画", "2K"),
    "hexi_defense": ("河西走廊场景：唐朝边防军在戈壁巡逻，落日余晖，苍凉壮阔，古风水墨画风", "2K"),
    "naval_jianghuai": ("江淮水师：唐朝战船在长江上列阵，水军操练，气势恢宏，古风插画", "2K"),
    "imperial_guard": ("唐朝禁军：金甲武士守卫宫门，精锐部队整装待发，威严壮观，古风工笔画", "2K"),
    # 河朔联络
    "contact_resistance": ("河北平原夜景：唐朝密使与义军首领在篝火旁密谈，联络抗燕，古风水墨画风", "2K"),
    "divide_yan": ("燕军大帐场景：叛军将领之间暗流涌动，离间计谋划，暗色调，古风插画", "2K"),
    "recruit_hebei": ("河北乡间：唐朝官员在村中招抚流民参军，百姓围观，古风画风", "2K"),
    "heshuo_negotiate": ("唐朝使臣与藩镇将领在厅堂中对坐谈判，各怀心思，古风工笔画风", "2K"),
    "rebellion_pardon": ("唐朝皇帝下诏赦免叛军降将的场景，金殿宣诏，庄重肃穆，古风插画", "2K"),
    # 财赋民生
    "secure_grain_route": ("大运河漕运：满载粮食的漕船在运河上航行，两岸繁华，古风山水画风", "2K"),
    "relieve_guanzhong": ("关中赈灾：唐朝官员在城门口向饥民施粥，民众感恩，古风插画", "2K"),
    "land_survey": ("古代清丈田亩场景：官员带领差役在田间测量土地，丈量工具摆放，古风工笔画", "2K"),
    "salt_tax_reform": ("唐朝盐铁衙门：官员在计算盐税账册，整顿财税，古风插画", "2K"),
    "trade_silk_road": ("丝绸之路：驼队在沙漠中行进，商旅络绎，繁荣盛景，古风山水画风", "2K"),
}

ACT_ENDING_PROMPTS = {
    "act1": ("潼关大战全景：唐军与燕军在潼关下激战，烽火连天，壮烈史诗般的战争场面，古风油画风格，气势磅礴", "2K"),
    "act2": ("唐朝新帝在灵武登基的场景：临时行宫中百官朝贺，新天子端坐龙椅，庄重肃穆中透着希望，古风工笔画", "2K"),
    "act3": ("唐军收复长安的凯旋场景：大军入城，百姓夹道欢呼，长安城门上的大唐旗帜重新飘扬，辉煌壮丽，古风插画", "2K"),
    "act4": ("河朔战场风云变幻：唐军与叛军在河北平原对峙，阴云密布中透着微光，暗示战局反复，古风水墨画风", "2K"),
    "act5": ("天下平定后的长安城全景：和平降临，城楼上的夕阳余晖，大唐国旗在晚风中微微飘扬，宁静而深远，古风山水画", "2K"),
}

NAV_ICON_PROMPTS = {
    "court": ("中国古代朝堂大殿内部场景，百官列队，金色龙椅位于中央，庄严华丽，图标风格，简约线条，圆形构图", "2K"),
    "overview": ("中国古代军事沙盘地图，红色和蓝色旗帜标记，帅旗飘扬，图标风格，圆形构图", "2K"),
    "map": ("中国古代天下地图，山川河流，九州标记，古雅色调，图标风格，圆形构图", "2K"),
    "army": ("中国古代兵器架，刀枪剑戟排列整齐，军旗背景，图标风格，简约有力，圆形构图", "2K"),
    "memorials": ("中国古代竹简与毛笔，奏章展开，朱砂批红，文房四宝，图标风格，典雅，圆形构图", "2K"),
    "policy": ("中国古代国策树图，枝繁叶茂的大树扎根于社稷之土，树叶上写有小字政策，图标风格，圆形构图", "2K"),
    "history": ("中国古代史官执笔记录，竹简堆积如山，烛光下书写，图标风格，深沉典雅，圆形构图", "2K"),
}


def batch_generate_policies(output_dir: str | Path) -> list[str]:
    """批量生成所有国策配图。返回已生成的文件列表。"""
    out = Path(output_dir) / "policies"
    out.mkdir(parents=True, exist_ok=True)
    generated = []
    for policy_id, (prompt, size) in POLICY_PROMPTS.items():
        target = out / f"{policy_id}.webp"
        if target.exists():
            generated.append(str(target))
            continue
        print(f"[国策] {policy_id} ...")
        if generate_and_save(prompt, target, size=size):
            generated.append(str(target))
            print(f"  OK {target.name}")
        else:
            print(f"  FAIL")
        time.sleep(1)
    return generated


def batch_generate_act_endings(output_dir: str | Path) -> list[str]:
    """批量生成五幕结局配图。"""
    out = Path(output_dir) / "endings"
    out.mkdir(parents=True, exist_ok=True)
    generated = []
    for act_id, (prompt, size) in ACT_ENDING_PROMPTS.items():
        target = out / f"{act_id}.webp"
        if target.exists():
            generated.append(str(target))
            continue
        print(f"[幕终] {act_id} ...")
        if generate_and_save(prompt, target, size=size):
            generated.append(str(target))
            print(f"  OK {target.name}")
        else:
            print(f"  FAIL")
        time.sleep(1)
    return generated


def batch_generate_nav_icons(output_dir: str | Path) -> list[str]:
    """批量生成左侧导航图标。"""
    out = Path(output_dir) / "nav"
    out.mkdir(parents=True, exist_ok=True)
    generated = []
    for tab_id, (prompt, size) in NAV_ICON_PROMPTS.items():
        target = out / f"{tab_id}.webp"
        if target.exists():
            generated.append(str(target))
            continue
        print(f"[导航] {tab_id} ...")
        if generate_and_save(prompt, target, size=size):
            generated.append(str(target))
            print(f"  OK {target.name}")
        else:
            print(f"  FAIL")
        time.sleep(1)
    return generated


def batch_generate_all(output_dir: str | Path = "apps/web/public/assets/generated") -> dict:
    """一键生成所有图片。返回各分类结果。"""
    return {
        "policies": batch_generate_policies(output_dir),
        "endings": batch_generate_act_endings(output_dir),
        "nav_icons": batch_generate_nav_icons(output_dir),
    }
