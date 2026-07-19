"""廷议与奏对路由。"""
from __future__ import annotations

import json
import re
import time
from dataclasses import asdict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from anshi.ai import generate_character_reply, load_config, parse_council_stance
from anshi.agents import create_court_script_agent, create_minister_agent, create_secretary_agent, run_agent, run_agent_stream
from anshi.campaign import ACT_NAMES
from anshi.conversation import context_for, record_exchange
from anshi.prompts import court_script_user, minister_user, secretary_user

router = APIRouter()

SCENE_KEYS = {"朝堂": "court", "密诏": "secret", "远奏": "remote", "court": "court", "secret": "secret", "remote": "remote"}


class AudienceRequest(BaseModel):
    character_id: str
    topic: str = "当前最紧要之事是什么？"
    scene: str = "朝堂"


class CouncilRequest(BaseModel):
    character_ids: list[str]
    topic: str = "当前最紧要之事是什么？"
    emperor_remark: str = ""
    previous_minutes: str = ""
    round_no: int = 1


def register(router_: APIRouter, game) -> None:
    """注册路由。game 是 GameState 闭包对象。"""
    CAMPAIGN = game.campaign_data

    @router_.post("/api/audience")
    def audience(request: AudienceRequest) -> dict:
        character = next((item for item in CAMPAIGN["characters"] if item["id"] == request.character_id), None)
        runtime_character = game.management.characters.get(request.character_id)
        if not character or not runtime_character or runtime_character.status != "active" or character["audience_status"] in {"enemy_only", "future_enemy", "player_character"}:
            return {"accepted": False, "detail": "此人当前不能入对或递交远奏。"}
        scene = SCENE_KEYS.get(request.scene)
        if not scene:
            return {"accepted": False, "detail": "奏对场景仅支持朝堂、密诏或远奏。"}
        started = time.perf_counter()
        reply, model_used = generate_character_reply(
            character, request.topic.strip() or "当前局势", scene,
            {"章节": ACT_NAMES[game.progress.act], "年月": f"{game.progress.year}年{game.progress.month}月",
             "事项": [asdict(issue) for issue in game.management.issues.values()],
             **context_for(game.conversation, character["id"])},
            with_status=True,
        )
        record_exchange(game.conversation, character["id"], request.topic, reply, request.scene, game.progress.total_turn)
        game.store.save_conversation(game.conversation)
        config = load_config(role="chat")
        game.store.record_agent_run("人物奏对", config.model if config else "中文模板", round((time.perf_counter() - started) * 1000), model_used, request.scene)
        return {"accepted": True, "scene": request.scene, "character_id": character["id"], "name": character["name"], "identity": character["identity"], "topic": request.topic, "reply": reply, "model_used": model_used}

    @router_.post("/api/council")
    def council(request: CouncilRequest) -> dict:
        selected = [item for item in CAMPAIGN["characters"] if item["id"] in request.character_ids][:6]
        selected = [item for item in selected if game.management.characters.get(item["id"]) and game.management.characters[item["id"]].status == "active"]
        if len(selected) < 2:
            return {"accepted": False, "detail": "朝议至少需要两名当前可用人物。"}
        world = {"章节": ACT_NAMES[game.progress.act], "年月": f"{game.progress.year}年{game.progress.month}月"}
        exchanges, speeches, prev_speech = [], [], ""
        for character in selected:
            char_ctx = context_for(game.conversation, character["id"])
            ctx = {**world, **char_ctx}
            agent = create_minister_agent(character, request.topic, ctx, round_no=request.round_no, previous_speech=prev_speech, minutes=request.previous_minutes, emperor_remark=request.emperor_remark)
            user_prompt = minister_user(character, request.topic, ctx, round_no=request.round_no, previous_speech=prev_speech, minutes=request.previous_minutes, emperor_remark=request.emperor_remark)
            fallback = f"【态度：保留】{character.get('name', '臣下')}：此事尚须细察。"
            reply, model_used = run_agent(agent, user_prompt, fallback=fallback, with_status=True)
            if not parse_council_stance(reply):
                reply = f"【态度：保留】{reply}"
            stance = parse_council_stance(reply)
            exchanges.append({"character_id": character["id"], "name": character["name"], "reply": reply, "stance": stance, "model_used": model_used})
            speeches.append({"name": character["name"], "reply": reply})
            prev_speech = f"{character['name']}：{reply}"
            record_exchange(game.conversation, character["id"], request.topic, reply, "廷议", game.progress.total_turn)
        is_final = request.round_no >= 2
        sec_agent = create_secretary_agent(request.topic, speeches, round_no=request.round_no, is_final=is_final)
        sec_prompt = secretary_user(request.topic, speeches, round_no=request.round_no, is_final=is_final)
        topic_q = "“" + request.topic + "”"
        sec_fallback = f"关于{topic_q}，群臣各陈己见，请陛下圣裁。" if is_final else f"关于{topic_q}，群臣已初步表态，尚存分歧。"
        minutes, _ = run_agent(sec_agent, sec_prompt, fallback=sec_fallback, with_status=True)
        game.store.save_conversation(game.conversation)
        return {"accepted": True, "topic": request.topic, "exchanges": exchanges, "minutes": minutes}

    @router_.post("/api/council/stream")
    def council_stream(request: CouncilRequest):
        selected = [item for item in CAMPAIGN["characters"] if item["id"] in request.character_ids][:6]
        selected = [item for item in selected if game.management.characters.get(item["id"]) and game.management.characters[item["id"]].status == "active"]
        if len(selected) < 2:
            def error_stream():
                yield f"data: {json.dumps({'error': '朝议至少需要两名当前可用人物。'}, ensure_ascii=False)}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")

        world = {"章节": ACT_NAMES[game.progress.act], "年月": f"{game.progress.year}年{game.progress.month}月"}
        round_no = request.round_no
        is_final = round_no >= 2

        characters_with_profile = []
        for character in selected:
            mc = game.management.characters.get(character["id"])
            characters_with_profile.append({
                **character,
                "attributes": {"loyalty": getattr(mc, "loyalty", 50), "administration": max(getattr(mc, "ability", 50), 50), "military": 50},
            })

        char_contexts = [{**world, **context_for(game.conversation, c["id"])} for c in selected]

        def generate():
            script_agent = create_court_script_agent()
            script_prompt = court_script_user(
                request.topic, characters_with_profile, char_contexts[0] if char_contexts else {},
                round_no=round_no, previous_minutes=request.previous_minutes, emperor_remark=request.emperor_remark,
            )
            yield f"data: {json.dumps({'type': 'council_start', 'topic': request.topic, 'round': round_no}, ensure_ascii=False)}\n\n"

            delimiter_re = re.compile(r"<<<臣:([^>\n]+)>>>")
            pending_text = ""
            current_speaker = ""
            current_content: list[str] = []
            speeches: list[dict] = []
            allowed_names = {c["name"] for c in selected}
            fallback_speaker = selected[0]["name"]

            def flush_speech():
                nonlocal current_speaker, current_content
                content = "".join(current_content).strip()
                if current_speaker and content:
                    speeches.append({"name": current_speaker, "reply": content})
                    yield f"data: {json.dumps({'type': 'speech_end', 'name': current_speaker, 'reply': content, 'round': round_no}, ensure_ascii=False)}\n\n"
                current_speaker = ""
                current_content = []

            def process_pending():
                nonlocal pending_text, current_speaker, current_content
                while pending_text:
                    match = delimiter_re.search(pending_text)
                    if match:
                        before = pending_text[:match.start()]
                        if before and current_speaker:
                            current_content.append(before)
                            yield f"data: {json.dumps({'type': 'speech_delta', 'name': current_speaker, 'delta': before}, ensure_ascii=False)}\n\n"
                        # If text before first delimiter and no speaker yet, assign to first selected
                        if before and not current_speaker:
                            current_speaker = fallback_speaker
                            current_content.append(before)
                            yield f"data: {json.dumps({'type': 'speech_start', 'name': current_speaker, 'round': round_no}, ensure_ascii=False)}\n\n"
                            yield f"data: {json.dumps({'type': 'speech_delta', 'name': current_speaker, 'delta': before}, ensure_ascii=False)}\n\n"
                        for item in flush_speech():
                            yield item
                        new_speaker = match.group(1).strip()
                        current_speaker = new_speaker if new_speaker in allowed_names else fallback_speaker
                        current_content = []
                        yield f"data: {json.dumps({'type': 'speech_start', 'name': current_speaker, 'round': round_no}, ensure_ascii=False)}\n\n"
                        pending_text = pending_text[match.end():]
                        continue
                    marker_start = pending_text.find("<<<臣:")
                    if marker_start >= 0:
                        if marker_start > 0:
                            before = pending_text[:marker_start]
                            if current_speaker:
                                current_content.append(before)
                                yield f"data: {json.dumps({'type': 'speech_delta', 'name': current_speaker, 'delta': before}, ensure_ascii=False)}\n\n"
                            elif before.strip():
                                # Text before first partial delimiter — assign to first speaker
                                current_speaker = fallback_speaker
                                current_content.append(before)
                                yield f"data: {json.dumps({'type': 'speech_start', 'name': current_speaker, 'round': round_no}, ensure_ascii=False)}\n\n"
                                yield f"data: {json.dumps({'type': 'speech_delta', 'name': current_speaker, 'delta': before}, ensure_ascii=False)}\n\n"
                            pending_text = pending_text[marker_start:]
                            continue
                        break
                    if current_speaker:
                        current_content.append(pending_text)
                        yield f"data: {json.dumps({'type': 'speech_delta', 'name': current_speaker, 'delta': pending_text}, ensure_ascii=False)}\n\n"
                    elif pending_text.strip():
                        # No speaker yet — assign to first selected
                        current_speaker = fallback_speaker
                        current_content.append(pending_text)
                        yield f"data: {json.dumps({'type': 'speech_start', 'name': current_speaker, 'round': round_no}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'speech_delta', 'name': current_speaker, 'delta': pending_text}, ensure_ascii=False)}\n\n"
                    pending_text = ""

            try:
                for chunk in run_agent_stream(script_agent, script_prompt, tag="朝会编剧"):
                    pending_text += chunk
                    for item in process_pending():
                        yield item
            except Exception:
                pass
            for item in process_pending():
                yield item
            for item in flush_speech():
                yield item

            if not speeches:
                for character in selected:
                    ctx = {**world, **context_for(game.conversation, character["id"])}
                    agent = create_minister_agent(character, request.topic, ctx, round_no=round_no, previous_speech="", minutes=request.previous_minutes, emperor_remark=request.emperor_remark)
                    user_prompt = minister_user(character, request.topic, ctx, round_no=round_no, previous_speech="", minutes=request.previous_minutes, emperor_remark=request.emperor_remark)
                    fallback = f"【态度：保留】{character.get('name', '臣下')}：此事尚须细察。"
                    reply, _ = run_agent(agent, user_prompt, fallback=fallback, with_status=True, tag=f"廷议-{character['name']}")
                    speeches.append({"name": character["name"], "reply": reply})
                    yield f"data: {json.dumps({'type': 'speech_start', 'name': character['name'], 'round': round_no}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'speech_end', 'name': character['name'], 'reply': reply, 'round': round_no}, ensure_ascii=False)}\n\n"

            for speech in speeches:
                character = next((c for c in selected if c["name"] == speech["name"]), None)
                if character:
                    record_exchange(game.conversation, character["id"], request.topic, speech["reply"], "廷议", game.progress.total_turn)

            sec_agent = create_secretary_agent(request.topic, speeches, round_no=round_no, is_final=is_final)
            sec_prompt = secretary_user(request.topic, speeches, round_no=round_no, is_final=is_final)
            topic_q = "“" + request.topic + "”"
            sec_fallback = f"关于{topic_q}，群臣各陈己见，请陛下圣裁。" if is_final else f"关于{topic_q}，群臣已初步表态，尚存分歧。"
            minutes, _ = run_agent(sec_agent, sec_prompt, fallback=sec_fallback, with_status=True, tag="中书舍人纪要")
            yield f"data: {json.dumps({'type': 'minutes', 'round': 'final' if is_final else round_no, 'text': minutes}, ensure_ascii=False)}\n\n"
            game.store.save_conversation(game.conversation)
            yield f"data: {json.dumps({'type': 'emperor_options', 'is_final': is_final}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    @router_.post("/api/secret-edicts")
    def secret_edict(request: SecretEdictRequest) -> dict:
        from anshi.campaign import add_secret_edict
        character = next((item for item in CAMPAIGN["characters"] if item["id"] == request.character_id), None)
        runtime_character = game.management.characters.get(request.character_id)
        if not character or not runtime_character or runtime_character.status != "active" or not request.text.strip():
            return {"accepted": False, "detail": "密诏必须指定可用人物并写明内容。"}
        with game.lock:
            edict = add_secret_edict(game.progress, character["name"], request.text, request.purpose)
            game.store.save_progress(game.progress)
            return {"accepted": True, "edict": edict, "progress": asdict(game.progress)}


class SecretEdictRequest(BaseModel):
    character_id: str
    text: str
    purpose: str = "军情"
