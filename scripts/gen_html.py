#!/usr/bin/env python3
"""Generate docs/介绍文档.html with base64-embedded images."""
import base64, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def b64(path):
    with open(path, 'rb') as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode()

IMG = {}
for name, path in {
    'act1': 'apps/web/public/assets/backgrounds/act_1.webp',
    'act2': 'apps/web/public/assets/backgrounds/act_2.webp',
    'act3': 'apps/web/public/assets/backgrounds/act_3.webp',
    'act4': 'apps/web/public/assets/backgrounds/act_4.webp',
    'act5': 'apps/web/public/assets/backgrounds/act_5.webp',
    'terrain': 'apps/web/public/assets/backgrounds/tang-terrain.webp',
    'court': 'apps/web/public/assets/backgrounds/court-hall.webp',
    'secret': 'apps/web/public/assets/backgrounds/secret-chamber.webp',
    'remote': 'apps/web/public/assets/backgrounds/remote-memorial.webp',
    'army': 'apps/web/public/assets/backgrounds/army-command.webp',
    'policy': 'apps/web/public/assets/backgrounds/policy-hall.webp',
    'lingbao': 'apps/web/public/assets/events/lingbao_battle.webp',
    'mawei': 'apps/web/public/assets/events/mawei_mutiny.webp',
    'hold': 'apps/web/public/assets/events/hold_tongguan.webp',
    'suiyang': 'apps/web/public/assets/events/suiyang_siege.webp',
    'tibet': 'apps/web/public/assets/events/tibet_changan_threat.webp',
    'uighur': 'apps/web/public/assets/events/uighur_treaty.webp',
    'shi': 'apps/web/public/assets/events/shi_siming_assassination.webp',
    'recap': 'apps/web/public/assets/events/recapture_capitals.webp',
    'heshuo': 'apps/web/public/assets/events/heshuo_surrender.webp',
    'lingwu': 'apps/web/public/assets/events/lingwu_accession.webp',
    'xuanzong': 'apps/web/public/assets/portraits/xuanzong.webp',
    'geshu': 'apps/web/public/assets/portraits/geshu_han.webp',
    'yang': 'apps/web/public/assets/portraits/yang_guozhong.webp',
    'guo': 'apps/web/public/assets/portraits/guo_ziyi.webp',
    'an': 'apps/web/public/assets/portraits/an_lushan.webp',
    'gao': 'apps/web/public/assets/portraits/gao_lishi.webp',
    'liheng': 'apps/web/public/assets/portraits/li_heng.webp',
    'liguangbi': 'apps/web/public/assets/portraits/li_guangbi.webp',
    'edict': 'apps/web/public/assets/ui/edict-paper.webp',
    'decision': 'apps/web/public/assets/ui/decision-scroll.webp',
}.items():
    IMG[name] = b64(path)

html = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>安史之乱：中唐续命 | 项目介绍</title>
<style>
:root{--ink:#1e2420;--paper:#efe7d7;--red:#86352d;--jade:#294c42;--gold:#b99353;--night:#121b18;--wrap:min(1100px,calc(100% - 48px));}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--paper);font-family:"Source Han Serif SC","Noto Serif SC","Songti SC",serif;line-height:1.8}
.wrap{width:var(--wrap);margin:auto;padding:0 24px}
h1{font-size:clamp(40px,6vw,72px);line-height:1.1;margin:0}
h2{font-size:clamp(28px,3.5vw,42px);line-height:1.2;margin:0 0 16px}
h3{font-size:22px;margin:0 0 10px}
p{margin:0 0 14px;color:#3a4540}
.eyebrow{display:block;color:var(--red);font-size:12px;font-weight:700;letter-spacing:2px;margin-bottom:8px}
img{max-width:100%;height:auto;display:block}
.hero{position:relative;min-height:80vh;display:flex;align-items:flex-end;padding:60px 0;color:#f8efdf;background:linear-gradient(0deg,#0b1511cc,#0b151166),url('""" + IMG['act1'] + """') center/cover}
.hero h1 span{display:block;font-size:clamp(14px,2vw,22px);font-weight:400;color:#dfaea1;margin-top:12px}
.hero-facts{display:flex;gap:0;margin-top:32px;border-top:1px solid #e8dcc061}
.hero-facts div{flex:1;padding:16px;border-right:1px solid #e8dcc061}
.hero-facts b{display:block;color:#f0d296;font-size:28px}
.hero-facts small{color:#c8d0c9;font-size:12px}
section{padding:80px 0}
.section-title{margin-bottom:40px}
.section-title p{max-width:700px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.card{padding:24px;border:1px solid #c4b89a;background:var(--paper)}
.card-dark{padding:24px;border:1px solid #3a4a42;background:var(--night);color:#e0d8c8}
.card-dark h3{color:#f0e6d4}
.card-dark p{color:#b0bab3}
.thumb{position:relative;overflow:hidden;border:1px solid #a09070}
.thumb img{width:100%;height:220px;object-fit:cover}
.thumb figcaption{padding:10px 12px;font-size:12px;background:var(--paper)}
.portrait{text-align:center}
.portrait img{width:100%;aspect-ratio:3/4;object-fit:cover;object-position:top;border:1px solid #a09070}
.portrait b{display:block;margin-top:8px;font-size:14px}
.portrait small{color:#666;font-size:11px}
.scene-img{position:relative;min-height:320px;display:flex;align-items:flex-end;padding:24px;color:#f6ebd7;background-size:cover;background-position:center;border:1px solid #a09070}
.scene-img::after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,#111a17cc,transparent)}
.scene-img>*{position:relative;z-index:1}
.tag{display:inline-block;padding:3px 8px;border:1px solid var(--gold);color:var(--gold);font-size:11px;margin-bottom:10px;background:#17211ddd}
.loop-step{padding:20px;border-left:3px solid var(--gold);margin-bottom:16px}
.loop-step b{color:var(--red);font-size:13px}
.allow{display:inline-block;padding:6px 10px;margin:4px;background:#d3e0d5;border-left:3px solid #477766;font-size:12px}
.deny{display:inline-block;padding:6px 10px;margin:4px;background:#ead7ce;border-left:3px solid var(--red);font-size:12px}
.model-card{padding:24px;border:1px solid #c4b89a;background:var(--paper)}
.model-card code{display:block;margin-top:12px;padding-top:12px;border-top:1px solid #d0c4a8;font-size:12px;color:#555}
.dark{background:var(--night);color:#e0d8c8}
.dark p{color:#b0bab3}
.dark h2{color:#f0e6d4}
.dark .eyebrow{color:#e1b971}
.tint{background:#e4d7be}
footer{padding:40px 20px;color:#c5ccc4;background:var(--night);text-align:center}
footer b{color:#eee4d3;font-size:20px}
footer p{color:#aab5ac;font-size:12px;margin-top:8px}
@media(max-width:768px){.grid-2,.grid-3,.grid-4{grid-template-columns:1fr}.hero-facts{flex-wrap:wrap}.hero-facts div{flex:1 1 45%}}
</style>
</head>
<body>

<header class="hero">
<div class="wrap">
<span class="eyebrow">AI 驱动的历史策略游戏</span>
<h1>安史之乱<span>从潼关危局开始，用对话和诏书，重新推动这台失序的唐朝国家机器</span></h1>
<div class="hero-facts">
<div><b>756&mdash;763</b><small>五幕战役</small></div>
<div><b>43</b><small>可召见人物</small></div>
<div><b>18</b><small>战役事件</small></div>
<div><b>64</b><small>自动测试</small></div>
</div>
</div>
</header>

<main>

<section><div class="wrap">
<div class="section-title">
<span class="eyebrow">这是什么</span>
<h2>一个&ldquo;聊天治国&rdquo;的历史游戏</h2>
<p>你扮演唐朝皇帝，召见大臣问策、组织群臣辩论、亲笔写诏书、裁决军国大事。大臣们会根据自己的立场、派系和利益回应你&mdash;&mdash;有的附和，有的反驳，有的暗中使绊。你做的每个决定都会影响下一回合的钱粮、军心和天下局势。</p>
</div>
<div class="grid-2">
<div><img src="IMG_TERRAIN" alt="天下形势图" style="border:1px solid #a09070"></div>
<div>
<h3>不是看历史，是亲手处理历史</h3>
<p>天宝十五载，安禄山已经在洛阳称帝，潼关守军内部互相猜忌，朝廷催战不止。你接过这个烂摊子：信谁？问谁？先救哪里？钱从哪来？</p>
<p>游戏里没有&ldquo;点击选项A获得+10民心&rdquo;这种预制按钮。你用自然语言和大臣对话，自己写诏书，AI帮你润色成唐朝风格的圣旨，再由程序检查哪些能执行、哪些不行。</p>
<p><strong>AI负责让角色说话、让世界做出反应；程序规则负责算钱粮、兵力和结局。</strong></p>
</div>
</div>
</div></section>

<section class="tint"><div class="wrap">
<div class="section-title">
<span class="eyebrow">怎么玩</span>
<h2>一局游戏的五个步骤</h2>
<p>每回合你按顺序做五件事。裁决不会立刻生效&mdash;&mdash;你可以先选了再慢慢考虑，最后一起结算。</p>
</div>
<div class="grid-3" style="grid-template-columns:repeat(5,1fr)">
<div class="card"><b style="color:var(--red);font-size:13px">第1步</b><h3>看局势</h3><p style="font-size:13px">打开地图，看看哪些地方在闹叛乱、哪支军队缺粮、前线情报是真是假。</p></div>
<div class="card"><b style="color:var(--red);font-size:13px">第2步</b><h3>问大臣</h3><p style="font-size:13px">单独召见或集体廷议。大臣会根据自己的官职、派系和立场说话，后面发言的人会回应前面的。</p></div>
<div class="card"><b style="color:var(--red);font-size:13px">第3步</b><h3>写诏书</h3><p style="font-size:13px">用大白话写下你的命令。AI会把它润色成唐朝风格的圣旨，并拆出可以执行的具体行动。</p></div>
<div class="card"><b style="color:var(--red);font-size:13px">第4步</b><h3>核议确认</h3><p style="font-size:13px">程序检查每个行动的目标对不对、投入合不合理。不通过的不会执行。</p></div>
<div class="card"><b style="color:var(--red);font-size:13px">第5步</b><h3>颁诏推进</h3><p style="font-size:13px">所有诏令、裁决一起结算。规则算钱粮兵力，AI推演天下反应，生成邸报。</p></div>
</div>
</div></section>

<section><div class="wrap">
<div class="section-title">
<span class="eyebrow">对话系统</span>
<h2>同一个大臣，在不同地方说不同的话</h2>
<p>游戏有三种对话场景，大臣在公开场合和私下说的话完全不一样。</p>
</div>
<div class="grid-3">
<div class="scene-img" style="background-image:url('IMG_COURT')"><div><span class="tag">公开朝堂</span><h3>朝堂奏对</h3><p style="color:#ddd;font-size:13px">满朝文武都在看着。大臣说话得顾及面子、派系和在场的人，不敢太直白。</p></div></div>
<div class="scene-img" style="background-image:url('IMG_SECRET')"><div><span class="tag">私下密谈</span><h3>密诏召对</h3><p style="color:#ddd;font-size:13px">只有你和他。大臣可以说真心话：谁不可信、哪里快撑不住了、该怎么暗中操作。</p></div></div>
<div class="scene-img" style="background-image:url('IMG_REMOTE')"><div><span class="tag">远方军报</span><h3>军镇远奏</h3><p style="color:#ddd;font-size:13px">边疆将领只能报告自己看到的。他会说&ldquo;消息可能已经过时了&rdquo;，不会假装知道朝廷的情况。</p></div></div>
</div>
<div style="margin-top:30px" class="grid-2">
<div class="scene-img" style="background-image:url('IMG_EDICT');min-height:240px"><div><span class="tag">诏书系统</span><h3>御笔拟诏</h3><p style="color:#ddd;font-size:13px">你用大白话写命令，AI润色成圣旨，再拆出可执行的行动清单让你确认。</p></div></div>
<div class="scene-img" style="background-image:url('IMG_DECISION');min-height:240px"><div><span class="tag">裁决系统</span><h3>御前裁决</h3><p style="color:#ddd;font-size:13px">重大事件需要你拍板。选了不会立刻生效，可以先放着，和其他诏令一起结算。</p></div></div>
</div>
</div></section>

<section class="dark"><div class="wrap">
<div class="section-title">
<span class="eyebrow">廷议系统</span>
<h2>一次调用，整场辩论</h2>
<p>选2到6个大臣入殿，AI会编排整场廷议：谁先发难、谁打断、谁回嘴、谁补台、谁逼皇帝拍板。后发言的人会读到前面的话，根据自己的立场决定附和还是反驳。</p>
</div>
<div class="grid-2">
<div><img src="IMG_COURT" alt="廷议场景" style="border:1px solid #3a4a42"></div>
<div>
<h3 style="color:#f0e6d4">为什么快？</h3>
<p>很多游戏让每个角色单独调一次AI，4个人就要等4次。我们只调一次，AI一口气输出整场辩论，用特殊标记分隔每个人的台词。所以廷议的速度和一个人对话差不多。</p>
<h3 style="color:#f0e6d4;margin-top:24px">大臣们会吵架吗？</h3>
<p>会。AI会根据人物的派系、性格和利益安排冲突&mdash;&mdash;有的当面反驳，有的暗讽，有的表面赞同其实设了条件，有的把责任推给别人。</p>
</div>
</div>
</div></section>

<section><div class="wrap">
<div class="section-title">
<span class="eyebrow">回合推演</span>
<h2>AI说了不算，规则说了才算</h2>
<p>这是整个游戏最关键的设计：AI可以提建议，但不能直接改数据。</p>
</div>
<div class="grid-2">
<div>
<h3>推演是怎么工作的？</h3>
<div class="loop-step"><b>第1步：规则先算</b><p style="font-size:13px">兵力、钱粮、行军路线、战斗结果&mdash;&mdash;这些由程序硬算，AI碰不了。</p></div>
<div class="loop-step"><b>第2步：AI提建议</b><p style="font-size:13px">AI看完规则算出的结果，提出&ldquo;民心可能会变&rdquo;&ldquo;某个将领可能有异心&rdquo;之类的软反应。</p></div>
<div class="loop-step"><b>第3步：程序审核</b><p style="font-size:13px">每个建议都要过检查：目标对不对？幅度合不合理？类型在不在白名单里？</p></div>
<div class="loop-step"><b>第4步：生成邸报</b><p style="font-size:13px">在同一次AI调用中，顺便生成一篇小说风格的邸报，讲述本回合的天下大势。</p></div>
</div>
<div>
<h3>AI能做什么、不能做什么</h3>
<div style="margin-bottom:16px">
<p style="font-size:13px;font-weight:700;margin-bottom:8px">可以提建议：</p>
<span class="allow">地区民心 / 动乱 / 城防</span>
<span class="allow">军队士气 / 补给</span>
<span class="allow">事项压力 / 进度</span>
<span class="allow">人物忠诚</span>
<span class="allow">NPC动向</span>
<span class="allow">事件伏线</span>
</div>
<div>
<p style="font-size:13px;font-weight:700;margin-bottom:8px">绝对不能碰：</p>
<span class="deny">现金、粮仓、兵力</span>
<span class="deny">日期与章节进度</span>
<span class="deny">战斗结果</span>
<span class="deny">不存在的目标</span>
</div>
</div>
</div>
</div></section>

<section class="tint"><div class="wrap">
<div class="section-title">
<span class="eyebrow">AI分工</span>
<h2>三个模型，各管一摊</h2>
<p>不是让一个AI干所有事。不同任务用不同的模型，各自配置、互不干扰。</p>
</div>
<div class="grid-3">
<div class="model-card"><span style="color:var(--red);font-size:12px">角色一</span><h3>人物议政模型</h3><p style="font-size:13px">管所有对话：朝堂奏对、密诏、远奏、多人廷议。它知道每个人的性格、立场和关系记忆。</p><code>输入：人物 + 场景 + 局势 + 前序发言<br>输出：角色台词<br>禁区：不能改数据、不能替你下命令</code></div>
<div class="model-card"><span style="color:var(--red);font-size:12px">角色二</span><h3>回合推演模型</h3><p style="font-size:13px">管天下反应：看完规则结算的结果，提出民心、士气、人物动向等软变化建议，同时生成邸报。</p><code>输入：硬结算后的全局状态<br>输出：JSON建议 + 邸报叙事<br>禁区：不能改兵力钱粮日期战果</code></div>
<div class="model-card"><span style="color:var(--red);font-size:12px">角色三</span><h3>文书与记忆模型</h3><p style="font-size:13px">管文书活：把你写的大白话润色成圣旨，拆出可执行的行动清单，还负责整理摘要和长期记忆。</p><code>输入：你的诏意 + 可用目标<br>输出：圣旨 + JSON行动候选<br>禁区：不能编造目标或越权执行</code></div>
</div>
</div></section>

<section><div class="wrap">
<div class="section-title">
<span class="eyebrow">43位人物</span>
<h2>三省六部、禁军边镇、安史燕廷</h2>
<p>每个人物都有立绘、官职、派系、立场和六维属性。他们会根据自己的利益和性格说话，不是橡皮图章。</p>
</div>
<div class="grid-4">
<div class="portrait"><img src="IMG_XUANZONG" alt="唐玄宗"><b>唐玄宗</b><small>天子</small></div>
<div class="portrait"><img src="IMG_GAO" alt="高力士"><b>高力士</b><small>内侍省</small></div>
<div class="portrait"><img src="IMG_YANG" alt="杨国忠"><b>杨国忠</b><small>宰相</small></div>
<div class="portrait"><img src="IMG_GESHU" alt="哥舒翰"><b>哥舒翰</b><small>潼关主帅</small></div>
<div class="portrait"><img src="IMG_GUO" alt="郭子仪"><b>郭子仪</b><small>朔方节度使</small></div>
<div class="portrait"><img src="IMG_LIGUANGBI" alt="李光弼"><b>李光弼</b><small>河东节度使</small></div>
<div class="portrait"><img src="IMG_LIHENG" alt="李亨"><b>李亨</b><small>太子</small></div>
<div class="portrait"><img src="IMG_AN" alt="安禄山"><b>安禄山</b><small>燕帝</small></div>
</div>
</div></section>

<section class="dark"><div class="wrap">
<div class="section-title">
<span class="eyebrow">事件画廊</span>
<h2>五幕战役的关键节点</h2>
<p>16张事件插图，覆盖从潼关失守到安史平定的每个重大转折。</p>
</div>
<div class="grid-3">
<figure class="thumb"><img src="IMG_LINGBAO" alt="灵宝之战" style="height:200px"><figcaption>灵宝之战 &middot; 哥舒翰出关惨败</figcaption></figure>
<figure class="thumb"><img src="IMG_MAWEI" alt="马嵬之变" style="height:200px"><figcaption>马嵬之变 &middot; 六军不发</figcaption></figure>
<figure class="thumb"><img src="IMG_HOLD" alt="潼关坚守" style="height:200px"><figcaption>潼关坚守 &middot; 固守待变</figcaption></figure>
<figure class="thumb"><img src="IMG_SUIYANG" alt="睢阳之战" style="height:200px"><figcaption>睢阳之战 &middot; 张巡死守</figcaption></figure>
<figure class="thumb"><img src="IMG_TIBET" alt="吐蕃入寇" style="height:200px"><figcaption>吐蕃入寇 &middot; 关中告急</figcaption></figure>
<figure class="thumb"><img src="IMG_UIGHUR" alt="回纥盟约" style="height:200px"><figcaption>回纥盟约 &middot; 借兵平叛</figcaption></figure>
<figure class="thumb"><img src="IMG_SHI" alt="史思明被弑" style="height:200px"><figcaption>燕廷弑主 &middot; 史思明被杀</figcaption></figure>
<figure class="thumb"><img src="IMG_RECAP" alt="收复两京" style="height:200px"><figcaption>收复两京 &middot; 反攻长安</figcaption></figure>
<figure class="thumb"><img src="IMG_HESHUO" alt="河朔归降" style="height:200px"><figcaption>河朔归降 &middot; 降而复叛</figcaption></figure>
</div>
</div></section>

<section><div class="wrap">
<div class="section-title">
<span class="eyebrow">场景美术</span>
<h2>11张场景背景</h2>
<p>朝堂、密室、军镇、国策厅、军令台&mdash;&mdash;每个界面都有专属背景。</p>
</div>
<div class="grid-3">
<figure class="thumb"><img src="IMG_COURT" alt="紫宸殿" style="height:200px"><figcaption>紫宸殿朝堂</figcaption></figure>
<figure class="thumb"><img src="IMG_SECRET" alt="密室" style="height:200px"><figcaption>密诏召对</figcaption></figure>
<figure class="thumb"><img src="IMG_REMOTE" alt="军镇" style="height:200px"><figcaption>军镇远奏</figcaption></figure>
<figure class="thumb"><img src="IMG_ARMY" alt="军令台" style="height:200px"><figcaption>军令台</figcaption></figure>
<figure class="thumb"><img src="IMG_POLICY" alt="国策厅" style="height:200px"><figcaption>国策厅</figcaption></figure>
<figure class="thumb"><img src="IMG_TERRAIN" alt="天下形势" style="height:200px"><figcaption>天下形势图</figcaption></figure>
</div>
</div></section>

<section class="tint"><div class="wrap">
<div class="section-title">
<span class="eyebrow">五幕战役</span>
<h2>从潼关到天下太平</h2>
<p>游戏跨越756&mdash;763年，分五幕推进。每一幕有新的事件、人物和地区解锁。</p>
</div>
<div class="grid-4" style="grid-template-columns:repeat(5,1fr)">
<div style="text-align:center"><img src="IMG_ACT1" alt="第一幕" style="height:100px;object-fit:cover;border:1px solid #a09070"><b style="display:block;margin-top:8px;font-size:13px">潼关危局</b><small style="font-size:11px;color:#666">756夏</small></div>
<div style="text-align:center"><img src="IMG_ACT2" alt="第二幕" style="height:100px;object-fit:cover;border:1px solid #a09070"><b style="display:block;margin-top:8px;font-size:13px">灵武即位</b><small style="font-size:11px;color:#666">756秋</small></div>
<div style="text-align:center"><img src="IMG_ACT3" alt="第三幕" style="height:100px;object-fit:cover;border:1px solid #a09070"><b style="display:block;margin-top:8px;font-size:13px">反攻长安</b><small style="font-size:11px;color:#666">757</small></div>
<div style="text-align:center"><img src="IMG_ACT4" alt="第四幕" style="height:100px;object-fit:cover;border:1px solid #a09070"><b style="display:block;margin-top:8px;font-size:13px">河朔反复</b><small style="font-size:11px;color:#666">758&mdash;759</small></div>
<div style="text-align:center"><img src="IMG_ACT5" alt="第五幕" style="height:100px;object-fit:cover;border:1px solid #a09070"><b style="display:block;margin-top:8px;font-size:13px">天下渐定</b><small style="font-size:11px;color:#666">760&mdash;763</small></div>
</div>
</div></section>

<section><div class="wrap">
<div class="section-title">
<span class="eyebrow">怎么做的</span>
<h2>AI全链路参与开发</h2>
<p>从调研、写代码、画图到测试，每一步都用了AI工具，但人始终做决策。</p>
</div>
<div class="grid-2">
<div>
<div class="card" style="margin-bottom:16px"><h3>前期：AI深度调研</h3><p style="font-size:13px">让AI研究安史之乱的历史细节：时间线、人物关系、地区军镇、钱粮制度。输出结构化数据，直接喂给游戏用。</p></div>
<div class="card" style="margin-bottom:16px"><h3>中期：多Agent并行开发</h3><p style="font-size:13px">用Codex拆任务、多个AI同时写不同模块的代码、Seedream批量生成43张人物立绘和16张事件图。</p></div>
<div class="card"><h3>后期：多模型混合迭代</h3><p style="font-size:13px">KIMI K2.7、小米MIMO V2.5、Claude Code混合使用&mdash;&mdash;每个模型干它最擅长的活。</p></div>
</div>
<div>
<h3>用到的AI工具</h3>
<div class="card-dark" style="margin-bottom:12px"><b style="color:#efcb85">调研阶段</b><p style="font-size:13px">AI深度研究 &rarr; 结构化JSON数据（历史、人物、数值）</p></div>
<div class="card-dark" style="margin-bottom:12px"><b style="color:#efcb85">开发阶段</b><p style="font-size:13px">Codex主Agent + 多子Agent并行（调研、内容、运行时、视觉）</p></div>
<div class="card-dark" style="margin-bottom:12px"><b style="color:#efcb85">美术阶段</b><p style="font-size:13px">Seedream 5.0批量生成 &rarr; 人工筛选 &rarr; 尺寸归一化</p></div>
<div class="card-dark"><b style="color:#efcb85">迭代阶段</b><p style="font-size:13px">KIMI K2.7 + MIMO V2.5 + Claude Code混合开发</p></div>
</div>
</div>
</div></section>

<!-- 推演架构 -->
<section><div class="wrap">
<div class="section-title">
<span class="eyebrow">推演架构</span>
<h2>AI说了不算，规则说了才算</h2>
<p>这是整个游戏最关键的设计：AI可以提建议，但不能直接改数据。</p>
</div>
<div class="grid-2">
<div>
<h3>推演是怎么工作的？</h3>
<div class="loop-step"><b>第1步：规则先算</b><p style="font-size:13px">兵力、钱粮、行军路线、战斗结果&mdash;&mdash;这些由程序硬算，AI碰不了。</p></div>
<div class="loop-step"><b>第2步：AI用工具查盘面</b><p style="font-size:13px">推演模型可以调用9个查询工具：查地区、查军队、查国库、查人物、查事项。先查清再提建议，不凭印象猜测。</p></div>
<div class="loop-step"><b>第3步：AI提建议</b><p style="font-size:13px">看完真实数据，提出民心、士气、人物动向等软变化建议。</p></div>
<div class="loop-step"><b>第4步：程序审核</b><p style="font-size:13px">每个建议都要过白名单检查：目标对不对？幅度合不合理？</p></div>
<div class="loop-step"><b>第5步：生成月末奏章</b><p style="font-size:13px">史官把结算数据写成白话史书风格的奏章，按军务/财政/地方/人事/待决五章组织。</p></div>
</div>
<div>
<h3>AI能做什么、不能做什么</h3>
<div style="margin-bottom:16px">
<p style="font-size:13px;font-weight:700;margin-bottom:8px">可以提建议：</p>
<span class="allow">地区民心 / 动乱 / 城防</span>
<span class="allow">军队士气 / 补给</span>
<span class="allow">事项压力 / 进度</span>
<span class="allow">人物忠诚</span>
<span class="allow">NPC动向</span>
<span class="allow">事件伏线</span>
</div>
<div>
<p style="font-size:13px;font-weight:700;margin-bottom:8px">绝对不能碰：</p>
<span class="deny">现金、粮仓、兵力</span>
<span class="deny">日期与章节进度</span>
<span class="deny">战斗结果</span>
<span class="deny">不存在的目标</span>
</div>
</div>
</div>
</div></section>

<!-- Tool-use -->
<section class="tint"><div class="wrap">
<div class="section-title">
<span class="eyebrow">Tool-Use</span>
<h2>推演模型可以查盘面</h2>
<p>不是把所有数据一股脑塞进prompt。推演模型有9个查询工具，按需查清再提建议。</p>
</div>
<div class="grid-3">
<div class="card"><h3>查地区</h3><p style="font-size:13px">list_regions / inspect_region(id)<br>查看16个地区的民心、动乱、城防、控制者。</p></div>
<div class="card"><h3>查军队</h3><p style="font-size:13px">list_armies / inspect_army(id)<br>查看各支军队的驻地、兵力、补给、士气。</p></div>
<div class="card"><h3>查国库</h3><p style="font-size:13px">check_treasury<br>查看现银、粮储、月收支。</p></div>
<div class="card"><h3>查人物</h3><p style="font-size:13px">list_characters / inspect_character(id)<br>查看在朝人物的官职、忠诚、能力。</p></div>
<div class="card"><h3>查事项</h3><p style="font-size:13px">list_issues<br>查看在办事项的紧张度、进度、承办人。</p></div>
<div class="card"><h3>查局势</h3><p style="font-size:13px">list_situations<br>查看潼关军令、关中粮储等局势进度。</p></div>
</div>
</div></section>

<!-- 事件效果 -->
<section><div class="wrap">
<div class="section-title">
<span class="eyebrow">事件效果</span>
<h2>不是关键词匹配，是AI理解</h2>
<p>玩家对事件做出选择后，AI会根据当前盘面生成具体效果，而不是硬编码的数值变化。</p>
</div>
<div class="grid-2">
<div>
<h3>之前（关键词匹配）</h3>
<div class="card" style="margin-bottom:12px">
<p style="font-size:13px"><b>玩家选：</b>全力救援睢阳</p>
<p style="font-size:13px"><b>程序做：</b>检测到"救援"和"全力"关键词</p>
<p style="font-size:13px"><b>结果：</b>固定扣120金、100粮</p>
<p style="font-size:13px;color:#888">问题：不管睢阳实际情况如何，效果都一样。</p>
</div>
</div>
<div>
<h3>现在（AI驱动）</h3>
<div class="card" style="margin-bottom:12px">
<p style="font-size:13px"><b>玩家选：</b>全力救援睢阳</p>
<p style="font-size:13px"><b>AI做：</b>先查睢阳（守军2000，民心35）、查附近军队（朔方军在河东）、查国库（金280）</p>
<p style="font-size:13px"><b>结果：</b>拨粮30给睢阳 + 调朔方军驰援</p>
<p style="font-size:13px;color:#477766">好处：效果贴合实际盘面，每次可能不同。</p>
</div>
</div>
</div>
</div></section>

<!-- 月末奏章 -->
<section class="dark"><div class="wrap">
<div class="section-title">
<span class="eyebrow">月末奏章</span>
<h2>白话史书风格的回合结算</h2>
<p>每回合结算后，史官会把本月发生的事写成一篇奏章，按五个章节组织，流式逐字显示给玩家。</p>
</div>
<div class="grid-2">
<div>
<h3 style="color:#f0e6d4">五章结构</h3>
<div class="card-dark" style="margin-bottom:8px"><b style="color:#efcb85">一、军务</b><p style="font-size:13px">军事动向、战况、调防、补给</p></div>
<div class="card-dark" style="margin-bottom:8px"><b style="color:#efcb85">二、财政</b><p style="font-size:13px">钱粮收支、国库变化</p></div>
<div class="card-dark" style="margin-bottom:8px"><b style="color:#efcb85">三、地方</b><p style="font-size:13px">各地民心、动乱、灾异</p></div>
<div class="card-dark" style="margin-bottom:8px"><b style="color:#efcb85">四、人事</b><p style="font-size:13px">任免、去职、人物动向</p></div>
<div class="card-dark"><b style="color:#efcb85">五、待决</b><p style="font-size:13px">未完成的事项、悬而未决的危机</p></div>
</div>
<div>
<h3 style="color:#f0e6d4">风格要求</h3>
<p>写"潼关守军粮尽，士卒日食一餐"，不写"补给降至35"。</p>
<p>写"朝廷拨粮三十石驰援睢阳，朔方军即日东进"，不写"朝廷采取了积极措施"。</p>
<p>每个段落以一个具体的场景或人物动作开篇，结尾留一句余韵暗示天下走向。</p>
</div>
</div>
</div></section>

<section class="dark"><div class="wrap">
<div class="section-title">
<span class="eyebrow">技术栈</span>
<h2>用了什么技术</h2>
</div>
<div class="grid-4">
<div class="card-dark"><b style="color:#efcb85">前端</b><p style="font-size:13px">React 19 + TypeScript + Vite<br>单文件SPA，流式渲染</p></div>
<div class="card-dark"><b style="color:#efcb85">后端</b><p style="font-size:13px">Python 3.13 + FastAPI<br>路由模块化，SSE流式输出</p></div>
<div class="card-dark"><b style="color:#efcb85">AI层</b><p style="font-size:13px">Agent工厂 + Tool-Use<br>供应商自动适配<br>流式 + JSON修复</p></div>
<div class="card-dark"><b style="color:#efcb85">存储</b><p style="font-size:13px">SQLite WAL<br>自动存档 + 手动存读档</p></div>
</div>
</div></section>

</main>

<footer>
<div class="wrap">
<b>安史之乱 &middot; 中唐续命</b>
<p>AI负责说话和反应，规则负责算账和结局。</p>
</div>
</footer>

</body>
</html>"""

# Replace placeholders with actual base64
replacements = {
    'IMG_TERRAIN': IMG['terrain'],
    'IMG_COURT': IMG['court'],
    'IMG_SECRET': IMG['secret'],
    'IMG_REMOTE': IMG['remote'],
    'IMG_ARMY': IMG['army'],
    'IMG_POLICY': IMG['policy'],
    'IMG_EDICT': IMG['edict'],
    'IMG_DECISION': IMG['decision'],
    'IMG_XUANZONG': IMG['xuanzong'],
    'IMG_GAO': IMG['gao'],
    'IMG_YANG': IMG['yang'],
    'IMG_GESHU': IMG['geshu'],
    'IMG_GUO': IMG['guo'],
    'IMG_LIGUANGBI': IMG['liguangbi'],
    'IMG_LIHENG': IMG['liheng'],
    'IMG_AN': IMG['an'],
    'IMG_LINGBAO': IMG['lingbao'],
    'IMG_MAWEI': IMG['mawei'],
    'IMG_HOLD': IMG['hold'],
    'IMG_SUIYANG': IMG['suiyang'],
    'IMG_TIBET': IMG['tibet'],
    'IMG_UIGHUR': IMG['uighur'],
    'IMG_SHI': IMG['shi'],
    'IMG_RECAP': IMG['recap'],
    'IMG_HESHUO': IMG['heshuo'],
    'IMG_ACT1': IMG['act1'],
    'IMG_ACT2': IMG['act2'],
    'IMG_ACT3': IMG['act3'],
    'IMG_ACT4': IMG['act4'],
    'IMG_ACT5': IMG['act5'],
}

for key, val in replacements.items():
    html = html.replace(key, val)

with open('docs/介绍文档.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written {len(html)} chars with {len(IMG)} images embedded")
