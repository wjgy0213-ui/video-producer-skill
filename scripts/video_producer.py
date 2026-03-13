#!/usr/bin/env python3
"""
Video Producer v1.0 — 全流程视频生产流水线
从选题到脚本到拍摄指南到提词器到多平台分发，一站式生成

用法 (CLI):
    python3 video_producer.py script --topic "AI员工体系" --style cognitive --duration 3
    python3 video_producer.py shoot --script script.md
    python3 video_producer.py teleprompter --script script.md
    python3 video_producer.py topics --niche "AI/一人公司" --count 10
    python3 video_producer.py adapt --script script.md --platforms xhs,douyin,youtube
    python3 video_producer.py analyze --script script.md
    python3 video_producer.py pipeline --topic "AI员工体系" --style cognitive --duration 3

用法 (API / JSON):
    echo '{"action":"pipeline","topic":"AI员工","style":"cognitive","duration":3}' | python3 video_producer.py --api
"""

import argparse
import json
import sys
import re
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"
SCRIPT_DIR = Path(__file__).parent

# ============================================================
# 视频风格定义
# ============================================================

VIDEO_STYLES = {
    "cognitive": {
        "name": "认知型",
        "name_en": "Cognitive/Insight",
        "desc": "打破常识、输出新认知、让观众感觉'原来如此'",
        "hook_pattern": "反认知开头 → 痛点共鸣 → 新认知输出 → 案例验证 → 价值升华",
        "best_for": "概念解释、趋势分析、行业洞察、新工具介绍",
        "tone": "真诚、有信念感、不急不慢",
        "pacing": "开头快(3-5s抓注意力) → 中段正常 → 结尾慢(真诚感)",
        "prep_mapping": {
            "P_open": "反认知钩子 / 数据冲击 / 场景代入",
            "R": "痛点放大 + 现有方案不足",
            "E": "核心认知输出 + 真实案例/数据",
            "P_close": "价值升华 + 行动号召",
        },
    },
    "tutorial": {
        "name": "教程型",
        "name_en": "Tutorial/How-To",
        "desc": "手把手教学，保姆级步骤拆解",
        "hook_pattern": "成果展示 → 工具/前置 → 分步教学 → 常见坑 → 总结",
        "best_for": "工具教学、操作指南、设置教程",
        "tone": "清晰、耐心、有条理",
        "pacing": "均匀节奏，每步停顿1-2秒让观众跟上",
        "prep_mapping": {
            "P_open": "成果预览 / '学完你也能...'",
            "R": "为什么要学 + 不学的代价",
            "E": "分步骤教学（录屏为主）",
            "P_close": "总结要点 + 收藏备用",
        },
    },
    "case_study": {
        "name": "案例型",
        "name_en": "Case Study/Demo",
        "desc": "真实案例展示，数据说话",
        "hook_pattern": "结果先行 → 背景铺垫 → 过程展示 → 关键转折 → 复盘总结",
        "best_for": "产品展示、实战复盘、数据公开",
        "tone": "真实、不吹不黑、数据导向",
        "pacing": "结果快闪 → 过程正常 → 关键点慢放",
        "prep_mapping": {
            "P_open": "成果数据冲击 / 反差对比",
            "R": "背景+挑战说明",
            "E": "完整案例展开 + 关键节点",
            "P_close": "复盘总结 + 可复制要点",
        },
    },
    "story": {
        "name": "故事型",
        "name_en": "Story/Narrative",
        "desc": "个人经历、蜕变故事、情感共鸣",
        "hook_pattern": "冲突开头 → 低谷 → 转折 → 成长 → 升华",
        "best_for": "个人品牌、情感共鸣、蜕变记录",
        "tone": "真诚、有温度、不表演",
        "pacing": "钩子快 → 低谷慢(共情) → 转折加速 → 升华慢(真诚)",
        "prep_mapping": {
            "P_open": "冲突/悬念开头",
            "R": "低谷铺垫 + 情绪共鸣",
            "E": "完整故事弧(转折是核心)",
            "P_close": "升华感悟 + 鼓励",
        },
    },
    "comparison": {
        "name": "对比型",
        "name_en": "Comparison/VS",
        "desc": "A vs B 深度对比，帮观众做选择",
        "hook_pattern": "对比悬念 → 维度拆解 → 逐项PK → 个人判断 → 总结",
        "best_for": "工具对比、策略对比、方案选择",
        "tone": "客观、有判断力、不骑墙",
        "pacing": "均匀，每个对比维度节奏一致",
        "prep_mapping": {
            "P_open": "'X和Y到底选哪个？'",
            "R": "为什么这个对比重要",
            "E": "多维度逐项对比",
            "P_close": "个人判断 + 适用场景建议",
        },
    },
    "list": {
        "name": "清单型",
        "name_en": "Listicle",
        "desc": "N个要点快速输出，信息密度高",
        "hook_pattern": "数量预告 → 逐个展开 → 彩蛋/最重要的一个 → 总结",
        "best_for": "工具推荐、避坑清单、必做列表",
        "tone": "紧凑、有节奏、不拖沓",
        "pacing": "每个点15-20秒，最后一个可以展开",
        "prep_mapping": {
            "P_open": "'N个你必须知道的...'",
            "R": "为什么这些很重要",
            "E": "逐个展开（每个:观点+理由+例子）",
            "P_close": "最重要的一个 + CTA",
        },
    },
}

# ============================================================
# 平台规格
# ============================================================

PLATFORM_SPECS = {
    "weishi": {
        "name": "视频号",
        "ratio": "9:16 竖屏 (1080×1920) 或 16:9 横屏",
        "duration": "1-15分钟（3-5分钟最佳）",
        "title_max": 30,
        "desc_max": 1000,
        "subtitle": "必须全程字幕",
        "font": "思源黑体/苹方",
        "music": "Lo-fi/轻科技，-18dB背景",
        "best_time": "20:00-22:00 CST（周五周六最佳）",
        "algo_tips": "完播率权重最高，前3秒决定命运；分享>评论>点赞",
        "tags_max": 5,
    },
    "xhs": {
        "name": "小红书视频",
        "ratio": "3:4 (1080×1440) 或 9:16 竖屏",
        "duration": "1-5分钟（2-3分钟最佳）",
        "title_max": 20,
        "desc_max": 1000,
        "subtitle": "必须全程字幕，关键词高亮",
        "font": "思源黑体，白字+黑边",
        "music": "轻快/治愈/科技感",
        "best_time": "20:00-22:00 CST",
        "algo_tips": "互动率>完播率，封面点击率是关键",
        "tags_max": 10,
        "sensitive": True,
    },
    "douyin": {
        "name": "抖音",
        "ratio": "9:16 竖屏 (1080×1920)",
        "duration": "15秒-10分钟（1-3分钟最佳）",
        "title_max": 55,
        "desc_max": None,
        "subtitle": "必须全程字幕",
        "font": "黑体/思源",
        "music": "热门BGM加权，可用抖音音乐库",
        "best_time": "12:00-13:00, 18:00-22:00 CST",
        "algo_tips": "完播率+互动率，DOU+可加速冷启动",
        "tags_max": 5,
    },
    "youtube": {
        "name": "YouTube",
        "ratio": "16:9 横屏 (1920×1080) 或 Shorts 9:16",
        "duration": "8-15分钟最佳（Shorts ≤60秒）",
        "title_max": 100,
        "desc_max": 5000,
        "subtitle": "推荐双语字幕（中+英）",
        "font": "Roboto/Noto Sans",
        "music": "YouTube Audio Library 免费曲库",
        "best_time": "PST 10AM-2PM (周二-周四)",
        "algo_tips": "CTR+观看时长，前30秒留存率决定推荐",
        "tags_max": 15,
    },
    "x": {
        "name": "X/Twitter 视频",
        "ratio": "16:9 或 1:1",
        "duration": "≤2:20（最佳30-60秒）",
        "title_max": 280,
        "desc_max": None,
        "subtitle": "必须内嵌字幕（大部分静音观看）",
        "font": "大号字，高对比",
        "music": "可选，多数人静音看",
        "best_time": "PST 6-9AM, 12-3PM",
        "algo_tips": "引用转推>点赞，争议性内容获得更多分发",
        "tags_max": 4,
    },
}

# ============================================================
# 选题评估维度
# ============================================================

TOPIC_SCORING = {
    "spread_potential": {"weight": 0.30, "label": "传播潜力", "desc": "能否引发转发/讨论"},
    "differentiation": {"weight": 0.25, "label": "差异化", "desc": "和现有内容的区别度"},
    "visual_appeal": {"weight": 0.20, "label": "可展示性", "desc": "有没有好的视觉素材"},
    "cognitive_value": {"weight": 0.15, "label": "认知价值", "desc": "看完后认知有没有升级"},
    "production_ease": {"weight": 0.10, "label": "制作难度", "desc": "录制和剪辑复杂度（越低越好）"},
}


# ============================================================
# 敏感词（小红书/抖音适用）
# ============================================================

SENSITIVE_WORDS = {
    '比特币': '🍪', 'BTC': '🍪', 'btc': '🍪', 'Bitcoin': '🍪',
    '以太坊': '姨太', 'ETH': '姨太', 'eth': '姨太',
    'USDT': 'U', 'USDC': 'U', '稳定币': 'U',
    '币安': 'BN', 'Binance': 'BN',
    '加密货币': '数字资产', '虚拟货币': '数字资产',
    '仓位': '位置', '建仓': '上车', '止损': '认错', '止盈': '落袋',
    '做多': '看多', '做空': '看空', '杠杆': '借力',
    '爆仓': '强制退出', '合约': '衍生品', '韭菜': '新手',
    '牛市': '上行周期', '熊市': '下行周期',
    'K线': '蜡烛图', '交易所': '平台', '挖矿': '产出',
    '割韭菜': '收割新手', '抄底': '低吸', '追高': '高位入场',
    '山寨币': '小币种',
}


def replace_sensitive(text: str) -> str:
    result = text
    for word, rep in sorted(SENSITIVE_WORDS.items(), key=lambda x: -len(x[0])):
        result = result.replace(word, rep)
    return result


# ============================================================
# 核心功能：脚本生成
# ============================================================

def generate_script(topic: str, style: str = "cognitive", duration: int = 3,
                    lang: str = "zh", niche: str = "AI/创业",
                    key_points: list = None, target_audience: str = None) -> dict:
    """
    生成完整视频脚本结构 + PREP 大纲

    Args:
        topic: 视频主题
        style: 视频风格 (cognitive/tutorial/case_study/story/comparison/list)
        duration: 目标时长（分钟）
        lang: 语言
        niche: 领域
        key_points: 必须包含的要点
        target_audience: 目标受众描述

    Returns: 完整脚本结构（段落时间分配 + PREP框架 + 画面建议 + 配乐建议）
    """
    vs = VIDEO_STYLES.get(style)
    if not vs:
        return {"error": f"Unknown style: {style}. Available: {list(VIDEO_STYLES.keys())}"}

    total_seconds = duration * 60

    # 时间分配（基于PREP框架）
    time_alloc = _calc_time_allocation(style, total_seconds)

    # 生成脚本结构
    script = {
        "version": VERSION,
        "topic": topic,
        "style": style,
        "style_name": vs["name"],
        "duration_target": f"{duration}分钟 ({total_seconds}秒)",
        "language": lang,
        "niche": niche,
        "target_audience": target_audience or "对AI/效率/创业感兴趣的人",

        "prep_framework": {
            "P_open": {
                "time": time_alloc["hook"],
                "goal": vs["prep_mapping"]["P_open"],
                "hooks": _gen_video_hooks(topic, style, lang),
                "visual": "出镜/快切画面/数据弹出",
                "energy": "HIGH — 前3秒决定去留",
                "tips": [
                    "第一句话必须制造好奇或冲突",
                    "不要自我介绍，直接进主题",
                    "语速比正常快10%",
                ],
            },
            "R": {
                "time": time_alloc["reason"],
                "goal": vs["prep_mapping"]["R"],
                "visual": "出镜+B-roll/截图",
                "energy": "MEDIUM — 建立共鸣",
                "structure": [
                    "铺垫痛点/背景（让观众点头'对对对'）",
                    "指出现有方案不足",
                    "引出你的方案/故事",
                ],
            },
            "E": {
                "time": time_alloc["example"],
                "goal": vs["prep_mapping"]["E"],
                "visual": _get_visual_suggestion(style),
                "energy": "MEDIUM-HIGH — 核心价值输出",
                "structure": _get_example_structure(style, duration),
            },
            "P_close": {
                "time": time_alloc["close"],
                "goal": vs["prep_mapping"]["P_close"],
                "visual": "回到出镜，全景收尾",
                "energy": "MEDIUM — 真诚有力量",
                "structure": [
                    "价值升华（连接更大的意义）",
                    "回扣开头（首尾呼应）",
                    "明确CTA（关注/评论/收藏）",
                ],
            },
        },

        "production_notes": {
            "pacing": vs["pacing"],
            "tone": vs["tone"],
            "music": {
                "style": "Lo-fi + 轻科技感" if niche in ["AI/创业", "科技", "AI"] else "根据内容调整",
                "volume": "-18dB 背景",
                "hook_section": "稍提高BGM能量",
                "close_section": "降低或去掉BGM（突出真诚）",
            },
            "subtitle": {
                "required": True,
                "font": "思源黑体 或 苹方",
                "highlight_color": "#22d3ee (青色) 或 #eab308 (金色)",
                "position": "画面下1/3",
                "size": "适配竖屏",
            },
            "transitions": {
                "default": "硬切 或 交叉溶解(0.3s)",
                "avoid": "花哨转场、星星、旋转等",
            },
            "recording_tips": [
                "分辨率至少 1920×1080",
                "录屏鼠标速度比平时慢30%",
                "出镜：中景偏近，半身",
                "光线：正面45°打光",
                "关闭所有通知和弹窗",
            ],
        },

        "key_points": key_points or [],
    }

    return script


def _calc_time_allocation(style: str, total_seconds: int) -> dict:
    """根据风格计算PREP各段时间分配"""
    ratios = {
        "cognitive":   {"hook": 0.10, "reason": 0.18, "example": 0.52, "close": 0.20},
        "tutorial":    {"hook": 0.08, "reason": 0.10, "example": 0.65, "close": 0.17},
        "case_study":  {"hook": 0.10, "reason": 0.15, "example": 0.55, "close": 0.20},
        "story":       {"hook": 0.10, "reason": 0.20, "example": 0.45, "close": 0.25},
        "comparison":  {"hook": 0.08, "reason": 0.12, "example": 0.60, "close": 0.20},
        "list":        {"hook": 0.08, "reason": 0.10, "example": 0.65, "close": 0.17},
    }
    r = ratios.get(style, ratios["cognitive"])
    result = {}
    for section, ratio in r.items():
        secs = int(total_seconds * ratio)
        m, s = divmod(secs, 60)
        result[section] = f"{secs}秒" if secs < 60 else f"{m}分{s:02d}秒"
    return result


def _gen_video_hooks(topic: str, style: str, lang: str) -> list:
    short = topic[:15]
    if lang == "zh":
        hooks = {
            "cognitive": [
                f"我一个人做公司，但每天有5个员工在帮我干活",
                f"关于{short}，我说一个可能让你不舒服的事实",
                f"90%的人对{short}的理解都是错的",
                f"3分钟搞懂{short}，少走3年弯路",
                f"如果你不懂{short}，你正在被时代淘汰",
            ],
            "tutorial": [
                f"跟着做，5分钟搞定{short}",
                f"全网最简单的{short}教程，看完就会",
                f"手把手教你{short}，零基础也能学会",
            ],
            "case_study": [
                f"我用{short}做了一个实验，结果出乎意料",
                f"真实数据公开：{short}到底有没有用？",
                f"{short}实测一个月，这是真实结果",
            ],
            "story": [
                f"从零开始到现在，我走了多少弯路",
                f"那一天，我差点放弃{short}",
                f"如果时间倒流，关于{short}我会这样做",
            ],
            "comparison": [
                f"A和B到底选哪个？深度对比告诉你",
                f"别再纠结了，{short}的终极对比来了",
            ],
            "list": [
                f"{short}必须知道的5件事",
                f"关于{short}，这6个坑千万别踩",
            ],
        }
    else:
        hooks = {
            "cognitive": [
                f"I run a one-person company with 5 AI employees",
                f"The uncomfortable truth about {topic}",
                f"90% of people get {topic} wrong. Here's why",
            ],
            "tutorial": [
                f"Set up {topic} in 5 minutes — step by step",
                f"The simplest {topic} tutorial you'll ever need",
            ],
            "case_study": [
                f"I tested {topic} for 30 days. Here are the real results",
                f"Real data: Does {topic} actually work?",
            ],
            "story": [
                f"How {topic} changed everything for me",
                f"I almost gave up on {topic}. Then this happened",
            ],
            "comparison": [
                f"A vs B: The definitive {topic} comparison",
            ],
            "list": [
                f"5 things about {topic} nobody tells you",
            ],
        }
    return hooks.get(style, hooks["cognitive"])


def _get_visual_suggestion(style: str) -> str:
    visuals = {
        "cognitive": "录屏(40%) + 出镜(30%) + 图表/动画(30%)",
        "tutorial": "录屏(70%) + 出镜(15%) + 图表(15%)",
        "case_study": "录屏/截图(50%) + 出镜(25%) + 数据图(25%)",
        "story": "出镜(60%) + B-roll(25%) + 文字卡(15%)",
        "comparison": "并列对比画面(40%) + 出镜(30%) + 图表(30%)",
        "list": "出镜(40%) + 图文卡片(40%) + B-roll(20%)",
    }
    return visuals.get(style, visuals["cognitive"])


def _get_example_structure(style: str, duration: int) -> list:
    structures = {
        "cognitive": [
            "核心概念介绍（'它是什么'）",
            "实际运作展示（'它怎么工作'）",
            "真实案例/数据（'效果如何'）",
            "与传统方案对比（'为什么更好'）",
        ],
        "tutorial": [
            "前置准备（工具/环境）",
            "步骤1: [操作] + 画面",
            "步骤2: [操作] + 画面",
            "步骤3: [操作] + 画面",
            "常见问题 & 避坑",
        ],
        "case_study": [
            "背景与挑战",
            "执行过程（关键节点）",
            "数据结果展示",
            "关键转折/发现",
            "可复制的要点",
        ],
        "story": [
            "起点/背景",
            "遇到的困难/低谷",
            "关键转折点",
            "成长与收获",
        ],
        "comparison": [
            "对比对象介绍",
            "维度1: [XX] 对比",
            "维度2: [XX] 对比",
            "维度3: [XX] 对比",
            "个人判断与建议",
        ],
        "list": [
            f"要点1: [标题] + 展开({15 if duration <= 2 else 20}秒)",
            f"要点2: [标题] + 展开({15 if duration <= 2 else 20}秒)",
            f"要点3: [标题] + 展开({15 if duration <= 2 else 20}秒)",
            f"要点4: [标题] + 展开(可加长)",
            f"要点5/彩蛋: [最重要的一个]",
        ],
    }
    return structures.get(style, structures["cognitive"])


# ============================================================
# 拍摄指南生成
# ============================================================

def generate_shooting_guide(script_data: dict = None, topic: str = "",
                            style: str = "cognitive", duration: int = 3) -> dict:
    """生成分镜表 + 素材清单 + 拍摄检查单"""

    if not script_data:
        script_data = generate_script(topic or "视频主题", style, duration)

    prep = script_data.get("prep_framework", {})
    total_secs = duration * 60

    # 分镜表
    shot_list = []
    current_time = 0

    # Hook镜头
    hook_secs = int(total_secs * 0.10)
    shot_list.append({
        "shot": 1, "time": f"0:00-0:{hook_secs:02d}",
        "type": "出镜", "framing": "中景偏近，半身",
        "content": "开头钩子（第一句话）",
        "audio": "画外音或同期声", "notes": "自信直接，不笑也OK",
    })

    # Reason镜头
    r_start = hook_secs
    r_secs = int(total_secs * 0.18)
    shot_list.append({
        "shot": 2, "time": f"0:{r_start:02d}-0:{r_start+r_secs//2:02d}",
        "type": "出镜", "framing": "中景",
        "content": "痛点共鸣段",
        "audio": "同期声", "notes": "表情稍认真，共情",
    })
    shot_list.append({
        "shot": 3, "time": f"0:{r_start+r_secs//2:02d}-0:{r_start+r_secs:02d}",
        "type": "B-roll/截图", "framing": "全屏",
        "content": "现有方案展示（快速切换）",
        "audio": "画外音", "notes": "可用多个截图快切",
    })

    # Example镜头（核心内容，占最多时间）
    e_start = r_start + r_secs
    e_secs = int(total_secs * 0.52)
    e_segments = 4
    seg_dur = e_secs // e_segments
    for i in range(e_segments):
        t_start = e_start + i * seg_dur
        t_end = t_start + seg_dur
        m_s, s_s = divmod(t_start, 60)
        m_e, s_e = divmod(t_end, 60)
        shot_list.append({
            "shot": 4 + i,
            "time": f"{m_s}:{s_s:02d}-{m_e}:{s_e:02d}",
            "type": "录屏" if i % 2 == 0 else "出镜+画外音",
            "framing": "全屏" if i % 2 == 0 else "中景",
            "content": f"核心内容段{i+1}",
            "audio": "画外音" if i % 2 == 0 else "同期声",
            "notes": "录屏鼠标慢移，让观众看清",
        })

    # Close镜头
    c_start = e_start + e_secs
    c_secs = total_secs - c_start
    m_cs, s_cs = divmod(c_start, 60)
    m_ce, s_ce = divmod(total_secs, 60)
    shot_list.append({
        "shot": 4 + e_segments,
        "time": f"{m_cs}:{s_cs:02d}-{m_ce}:{s_ce:02d}",
        "type": "出镜", "framing": "中景偏近",
        "content": "价值升华 + CTA",
        "audio": "同期声", "notes": "最重要！真诚、有力量",
    })

    guide = {
        "version": VERSION,
        "topic": script_data.get("topic", topic),
        "style": style,
        "duration": f"{duration}分钟",
        "shot_list": shot_list,
        "total_shots": len(shot_list),

        "pre_shoot_checklist": {
            "equipment": [
                "📱 手机/相机 + 三脚架",
                "💡 补光灯（正面45°打光）",
                "🎤 麦克风（有线耳机也行）",
                "🖥️ 电脑显示屏（录屏用）",
            ],
            "software": [
                "OBS 或 QuickTime（Mac 录屏）",
                "剪映/CapCut/DaVinci（剪辑）",
                "提词器 App（手机放镜头旁）",
            ],
            "environment": [
                "桌面整理干净",
                "显示器可见（增加真实感）",
                "关闭通知和弹窗",
                "背景不杂乱",
            ],
        },

        "recording_tips": {
            "screen_recording": [
                "分辨率 ≥1920×1080",
                "鼠标速度比平时慢30%",
                "切换视图时停顿1-2秒",
                "可用 ⌘+ 放大页面",
                "录屏时别说话（后期配画外音）",
            ],
            "on_camera": [
                "穿着简单干净",
                "镜头：中景偏近，半身",
                "光线：自然光或台灯补光",
                "语速：自然不急，偏真诚不偏表演",
                "表情：真实、轻松、有信念感",
            ],
        },

        "editing_guide": {
            "pacing": {
                "hook": "每3-5秒切一次画面（快节奏抓注意力）",
                "reason": "每5-8秒切（正常节奏）",
                "example": "按操作节奏切（录屏段）",
                "close": "少切，真诚感",
            },
            "transitions": "硬切或交叉溶解(0.3s)，不要花哨转场",
            "music": "-18dB背景，钩子段稍提高，升华段降低或去掉",
        },

        "time_estimate": {
            "screen_recording": "20-30 min",
            "screenshots": "5-10 min",
            "on_camera": "30-60 min (可能2-3遍)",
            "rough_cut": "30-45 min",
            "fine_cut_subtitle": "45-60 min",
            "export_publish": "15 min",
            "total": "2.5-4 小时",
        },
    }

    return guide


# ============================================================
# 提词器生成
# ============================================================

def generate_teleprompter(script_data: dict = None, topic: str = "",
                          style: str = "cognitive") -> dict:
    """从脚本结构生成纯文本提词器版本"""

    sections = []
    prep = script_data.get("prep_framework", {}) if script_data else {}

    if prep:
        sections.append({
            "label": "【钩子】",
            "instruction": "自信、直接、语速比平时快10%",
            "lines": prep.get("P_open", {}).get("hooks", [f"关于{topic}..."])[:2],
        })
        sections.append({
            "label": "【痛点/背景】",
            "instruction": "稍认真，共情",
            "lines": prep.get("R", {}).get("structure", ["痛点铺垫..."]),
        })
        sections.append({
            "label": "【核心内容】",
            "instruction": "切录屏段用画外音，出镜段自然讲述",
            "lines": prep.get("E", {}).get("structure", ["核心展开..."]),
        })
        sections.append({
            "label": "【升华+CTA】",
            "instruction": "真诚、有力量、语速放慢",
            "lines": prep.get("P_close", {}).get("structure", ["总结升华..."]),
        })
    else:
        sections.append({
            "label": "【提词器】",
            "instruction": "请先生成脚本，再生成提词器",
            "lines": [f"主题：{topic}"],
        })

    # 生成纯文本
    text_lines = []
    for sec in sections:
        text_lines.append(f"\n{'='*40}")
        text_lines.append(sec["label"])
        text_lines.append(f"（{sec['instruction']}）")
        text_lines.append(f"{'='*40}\n")
        for line in sec["lines"]:
            text_lines.append(line)
            text_lines.append("")

    return {
        "version": VERSION,
        "topic": script_data.get("topic", topic) if script_data else topic,
        "sections": sections,
        "plain_text": "\n".join(text_lines),
        "tips": [
            "手机放在镜头旁边，字号调到最大",
            "每段之间停顿1-2秒",
            "不需要逐字读，用自己的话讲",
            "关键数字/概念可以看一眼提词器确认",
        ],
    }


# ============================================================
# 选题队列生成
# ============================================================

def generate_topic_queue(niche: str = "AI/一人公司", count: int = 10,
                         lang: str = "zh", existing_topics: list = None) -> dict:
    """生成选题队列 + 评分 + 排期建议"""

    # 选题池模板（按领域）
    topic_pools = {
        "AI/一人公司": [
            {"topic": "我一个人，但有N个AI员工", "style": "cognitive", "score_hint": 92,
             "why": "强钩子+新认知+实操展示"},
            {"topic": "AI每天6点起床帮我干活", "style": "case_study", "score_hint": 85,
             "why": "自动化展示，满足好奇心"},
            {"topic": "N个AI，每个都不一样", "style": "cognitive", "score_hint": 82,
             "why": "Agent分工=新认知"},
            {"topic": "我的AI军团花了多少钱", "style": "cognitive", "score_hint": 88,
             "why": "反差钩子，成本透明=信任"},
            {"topic": "AI帮我省了20小时/周", "style": "case_study", "score_hint": 80,
             "why": "量化效率，有说服力"},
            {"topic": "AI做内容到底行不行", "style": "comparison", "score_hint": 78,
             "why": "真实展示AI内容质量"},
            {"topic": "我给AI搭了一个办公室", "style": "case_study", "score_hint": 86,
             "why": "视觉满足感强"},
            {"topic": "一个人管N个AI不累死吗", "style": "cognitive", "score_hint": 83,
             "why": "管理方法论=认知升级"},
            {"topic": "AI帮我交易，赚了还是亏了", "style": "case_study", "score_hint": 90,
             "why": "AI+交易=超高好奇心"},
            {"topic": "为什么你不应该只用ChatGPT", "style": "cognitive", "score_hint": 87,
             "why": "反认知+升维对比"},
            {"topic": "一人公司的AI工具栈完整公开", "style": "list", "score_hint": 81,
             "why": "工具推荐+干货收藏"},
            {"topic": "AI写代码vs人写代码", "style": "comparison", "score_hint": 79,
             "why": "热门话题+真实对比"},
            {"topic": "从0搭建你的第一个AI员工", "style": "tutorial", "score_hint": 76,
             "why": "保姆级教程，搜索流量"},
            {"topic": "AI帮我做了什么（每日vlog）", "style": "case_study", "score_hint": 74,
             "why": "日常+真实感"},
            {"topic": "一人公司年入X万的可能性", "style": "cognitive", "score_hint": 89,
             "why": "收入话题=最强钩子"},
        ],
        "交易/投资": [
            {"topic": "为什么90%的人在牛市也亏钱", "style": "cognitive", "score_hint": 91},
            {"topic": "我的交易系统完整公开", "style": "case_study", "score_hint": 87},
            {"topic": "新手最常犯的5个交易错误", "style": "list", "score_hint": 84},
            {"topic": "从爆仓到稳定盈利的真实经历", "style": "story", "score_hint": 88},
            {"topic": "交易日记怎么写才有用", "style": "tutorial", "score_hint": 77},
        ],
    }

    pool = topic_pools.get(niche, topic_pools["AI/一人公司"])

    # 过滤已有选题
    if existing_topics:
        pool = [t for t in pool if t["topic"] not in existing_topics]

    # 取前N个
    topics = pool[:count]

    # 排期建议
    schedule = []
    week = 1
    day_options = ["周三", "周五", "周六"]
    for i, t in enumerate(topics):
        day_idx = i % len(day_options)
        if day_idx == 0 and i > 0:
            week += 1
        schedule.append({
            "week": week,
            "day": day_options[day_idx],
            "topic": t["topic"],
            "style": t["style"],
        })

    return {
        "version": VERSION,
        "niche": niche,
        "topics": topics,
        "count": len(topics),
        "schedule": schedule,
        "scoring_criteria": TOPIC_SCORING,
        "recommendation": f"优先做评分最高的{min(3, len(topics))}个",
    }


# ============================================================
# 多平台适配
# ============================================================

def adapt_for_platforms(script_data: dict, platforms: list = None) -> dict:
    """将脚本适配到多个平台的发布规格"""

    if not platforms:
        platforms = ["weishi", "xhs", "douyin"]

    topic = script_data.get("topic", "")
    adaptations = {}

    for pf_id in platforms:
        spec = PLATFORM_SPECS.get(pf_id)
        if not spec:
            adaptations[pf_id] = {"error": f"Unknown platform: {pf_id}"}
            continue

        # 标题生成
        titles = _gen_platform_titles(topic, pf_id, spec.get("title_max", 30))

        # 描述/简介
        desc = _gen_platform_desc(topic, pf_id)

        # 标签
        tags = _gen_platform_tags(topic, pf_id)

        # 敏感词处理
        if spec.get("sensitive"):
            titles = [replace_sensitive(t) for t in titles]
            desc = replace_sensitive(desc)
            tags = [replace_sensitive(t) for t in tags]

        adaptations[pf_id] = {
            "platform": spec["name"],
            "specs": {
                "ratio": spec["ratio"],
                "duration": spec["duration"],
                "subtitle": spec["subtitle"],
            },
            "titles": titles,
            "description": desc,
            "tags": tags,
            "best_publish_time": spec["best_time"],
            "algo_tips": spec["algo_tips"],
            "cover_tips": _get_cover_tips(pf_id),
        }

    return {
        "version": VERSION,
        "topic": topic,
        "platforms": adaptations,
        "publish_order": _get_publish_order(platforms),
    }


def _gen_platform_titles(topic: str, platform: str, max_len: int) -> list:
    short = topic[:12]
    if platform in ["weishi", "xhs", "douyin"]:
        titles = [
            f"「{short}」一人公司的生存杠杆",
            f"别再{short[:8]}了！真相在这",
            f"3分钟搞懂{short}",
            f"关于{short}，90%人都想错了",
            f"{short}完整攻略",
        ]
    elif platform == "youtube":
        titles = [
            f"{topic} — The Complete Guide for Solo Founders",
            f"I Built {topic}. Here's What Happened.",
            f"Why {topic} Changes Everything for One-Person Companies",
        ]
    else:
        titles = [
            f"The truth about {topic}",
            f"{topic} — what nobody tells you",
        ]

    if max_len:
        titles = [t[:max_len] for t in titles]

    return titles


def _gen_platform_desc(topic: str, platform: str) -> str:
    if platform in ["weishi", "xhs", "douyin"]:
        return (
            f"关于{topic}的深度分享。\n"
            "如果你也对AI/效率/一人公司感兴趣，关注我，持续更新。\n"
            "有问题评论区聊 💬"
        )
    elif platform == "youtube":
        return (
            f"Deep dive into {topic}.\n"
            "If you're interested in AI, automation, and solo entrepreneurship, subscribe!\n"
            "Drop a comment with your questions."
        )
    return f"About {topic}."


def _gen_platform_tags(topic: str, platform: str) -> list:
    if platform in ["weishi", "xhs", "douyin"]:
        return ["#AI", "#一人公司", "#效率提升", "#自媒体", "#认知升级"]
    elif platform == "youtube":
        return ["#AI", "#solofounder", "#automation", "#productivity", "#onepersonbusiness"]
    elif platform == "x":
        return ["#AI", "#SoloFounder", "#BuildInPublic"]
    return []


def _get_cover_tips(platform: str) -> list:
    if platform in ["weishi", "xhs", "douyin"]:
        return [
            "暗色系科技风背景",
            "大字标题叠加（白字或青色字）",
            "人物出镜照或产品截图",
            "不过度设计，真实感>精致感",
        ]
    elif platform == "youtube":
        return [
            "高对比度，文字占画面30%+",
            "面部表情（惊讶/好奇）",
            "3词以内的标题关键词",
            "1280×720 最低分辨率",
        ]
    return ["简洁、高对比、文字清晰"]


def _get_publish_order(platforms: list) -> list:
    """发布顺序建议"""
    priority = {"weishi": 1, "xhs": 2, "douyin": 3, "youtube": 4, "x": 5}
    ordered = sorted(platforms, key=lambda p: priority.get(p, 99))
    order = []
    for i, p in enumerate(ordered):
        spec = PLATFORM_SPECS.get(p, {})
        order.append({
            "order": i + 1,
            "platform": spec.get("name", p),
            "timing": spec.get("best_time", ""),
            "note": "首发建立热度" if i == 0 else "跟发" if i < 3 else "延后发布",
        })
    return order


# ============================================================
# 脚本分析
# ============================================================

def analyze_script(text: str) -> dict:
    """分析视频脚本质量"""

    word_count = len(text)
    est_duration_sec = word_count / 4  # 中文约4字/秒
    est_duration_min = est_duration_sec / 60

    # PREP 结构检查
    has_hook = any(w in text[:200] for w in ["为什么", "如何", "90%", "千万", "不是", "别再", "其实", "我", "你"])
    has_reason = any(w in text for w in ["因为", "所以", "关键", "核心", "问题", "痛点"])
    has_example = any(w in text for w in ["比如", "举例", "来看", "给你看", "展示", "案例", "数据", "第一", "第二"])
    has_cta = any(w in text[-300:] for w in ["关注", "评论", "点赞", "收藏", "一起", "分享", "follow", "subscribe"])

    structure_score = sum([
        25 if has_hook else 0,
        20 if has_reason else 0,
        35 if has_example else 0,
        20 if has_cta else 0,
    ])

    # 节奏检查
    paragraphs = [p for p in text.split('\n') if p.strip()]
    avg_para_len = sum(len(p) for p in paragraphs) / max(len(paragraphs), 1)

    # 口语化检查
    spoken_words = ["你", "我", "吧", "呢", "啊", "嘛", "对吧", "其实", "就是"]
    spoken_count = sum(text.count(w) for w in spoken_words)
    spoken_ratio = spoken_count / max(word_count / 100, 1)

    grade = (
        "S" if structure_score >= 85 else
        "A" if structure_score >= 70 else
        "B" if structure_score >= 50 else
        "C" if structure_score >= 35 else "D"
    )

    suggestions = []
    if not has_hook:
        suggestions.append("🎯 开头缺少强钩子 — 前3秒要制造好奇或冲突")
    if not has_reason:
        suggestions.append("🔥 缺少'为什么重要'的论证 — 加入痛点/动机")
    if not has_example:
        suggestions.append("📖 缺少具体案例/步骤 — 加入展示/数据/拆解")
    if not has_cta:
        suggestions.append("🎬 结尾缺少CTA — 加入关注/评论/收藏引导")
    if avg_para_len > 80:
        suggestions.append("✂️ 段落太长 — 视频脚本每段控制在2-3句")
    if spoken_ratio < 2:
        suggestions.append("💬 口语感不足 — 加入'你''我''对吧'等口语词")

    return {
        "version": VERSION,
        "word_count": word_count,
        "estimated_duration": f"{est_duration_min:.1f}分钟",
        "structure_score": structure_score,
        "grade": grade,
        "structure_check": {
            "hook": "✅" if has_hook else "❌",
            "reason": "✅" if has_reason else "❌",
            "example": "✅" if has_example else "❌",
            "cta": "✅" if has_cta else "❌",
        },
        "readability": {
            "avg_paragraph_length": f"{avg_para_len:.0f}字",
            "total_paragraphs": len(paragraphs),
            "spoken_ratio": f"{spoken_ratio:.1f}/100字",
        },
        "suggestions": suggestions or ["✅ 脚本结构完整，可以录制！"],
    }


# ============================================================
# 全流水线
# ============================================================

def run_pipeline(topic: str, style: str = "cognitive", duration: int = 3,
                 platforms: list = None, lang: str = "zh",
                 niche: str = "AI/创业") -> dict:
    """一键生成全套视频生产物料"""

    # 1. 生成脚本
    script = generate_script(topic, style, duration, lang, niche)

    # 2. 生成拍摄指南
    guide = generate_shooting_guide(script, topic, style, duration)

    # 3. 生成提词器
    teleprompter = generate_teleprompter(script, topic, style)

    # 4. 多平台适配
    if not platforms:
        platforms = ["weishi", "xhs", "douyin"]
    adaptation = adapt_for_platforms(script, platforms)

    return {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(),
        "topic": topic,
        "style": style,
        "duration": f"{duration}分钟",

        "deliverables": {
            "script": script,
            "shooting_guide": guide,
            "teleprompter": teleprompter,
            "platform_adaptation": adaptation,
        },

        "next_steps": [
            "1. 审核脚本内容，调整措辞和重点",
            "2. 按拍摄指南准备设备和环境",
            "3. 打开提词器，开始录制",
            "4. 按剪辑指南完成后期",
            "5. 按平台适配方案发布",
        ],
    }


# ============================================================
# API 入口
# ============================================================

def handle_api(input_data: dict) -> dict:
    """统一 API 入口"""
    action = input_data.get("action", "pipeline")

    # SkillPay 计费
    PAID_ACTIONS = {"pipeline": 1.0, "script": 0.5, "shooting_guide": 0.5,
                    "topics": 0.5, "adapt": 0.5, "analyze": 0.5}
    if action in PAID_ACTIONS and input_data.get("user_id"):
        try:
            from skillpay import charge
            billing = charge(
                user_id=input_data["user_id"],
                amount=PAID_ACTIONS[action],
                description=f"Video Producer {action}",
            )
            if not billing["success"] and billing.get("mode") != "free":
                return {
                    "error": "payment_required",
                    "payment_url": billing.get("payment_url"),
                    "message": billing.get("message"),
                }
        except ImportError:
            pass

    if action == "pipeline":
        return run_pipeline(
            topic=input_data.get("topic", ""),
            style=input_data.get("style", "cognitive"),
            duration=input_data.get("duration", 3),
            platforms=input_data.get("platforms"),
            lang=input_data.get("lang", "zh"),
            niche=input_data.get("niche", "AI/创业"),
        )
    elif action == "script":
        return generate_script(
            topic=input_data.get("topic", ""),
            style=input_data.get("style", "cognitive"),
            duration=input_data.get("duration", 3),
            lang=input_data.get("lang", "zh"),
            niche=input_data.get("niche", "AI/创业"),
            key_points=input_data.get("key_points"),
            target_audience=input_data.get("target_audience"),
        )
    elif action == "shooting_guide":
        return generate_shooting_guide(
            topic=input_data.get("topic", ""),
            style=input_data.get("style", "cognitive"),
            duration=input_data.get("duration", 3),
        )
    elif action == "teleprompter":
        script = generate_script(
            topic=input_data.get("topic", ""),
            style=input_data.get("style", "cognitive"),
            duration=input_data.get("duration", 3),
        )
        return generate_teleprompter(script)
    elif action == "topics":
        return generate_topic_queue(
            niche=input_data.get("niche", "AI/一人公司"),
            count=input_data.get("count", 10),
            lang=input_data.get("lang", "zh"),
            existing_topics=input_data.get("existing_topics"),
        )
    elif action == "adapt":
        script = generate_script(
            topic=input_data.get("topic", ""),
            style=input_data.get("style", "cognitive"),
            duration=input_data.get("duration", 3),
        )
        return adapt_for_platforms(
            script, input_data.get("platforms"),
        )
    elif action == "analyze":
        text = input_data.get("text", "")
        if not text and input_data.get("file"):
            p = Path(input_data["file"])
            if p.exists():
                text = p.read_text()
        if not text:
            return {"error": "No script text provided"}
        return analyze_script(text)
    elif action == "styles":
        return {"styles": [
            {"id": k, "name": v["name"], "name_en": v["name_en"],
             "desc": v["desc"], "best_for": v["best_for"]}
            for k, v in VIDEO_STYLES.items()
        ]}
    elif action == "platforms":
        return {"platforms": [
            {"id": k, "name": v["name"], "ratio": v["ratio"],
             "duration": v["duration"], "best_time": v["best_time"]}
            for k, v in PLATFORM_SPECS.items()
        ]}
    elif action == "version":
        return {"version": VERSION, "name": "Video Producer"}
    else:
        return {"error": f"Unknown action: {action}",
                "available": ["pipeline", "script", "shooting_guide", "teleprompter",
                              "topics", "adapt", "analyze", "styles", "platforms", "version"]}


def main():
    parser = argparse.ArgumentParser(description=f'Video Producer v{VERSION}')
    parser.add_argument('--api', action='store_true', help='API模式：从stdin读取JSON')

    sub = parser.add_subparsers(dest='command')

    # pipeline
    pipe = sub.add_parser('pipeline', help='全流水线生成')
    pipe.add_argument('--topic', '-t', required=True)
    pipe.add_argument('--style', '-s', default='cognitive', choices=list(VIDEO_STYLES.keys()))
    pipe.add_argument('--duration', '-d', type=int, default=3)
    pipe.add_argument('--platforms', '-p', default='weishi,xhs,douyin')

    # script
    scr = sub.add_parser('script', help='生成脚本')
    scr.add_argument('--topic', '-t', required=True)
    scr.add_argument('--style', '-s', default='cognitive', choices=list(VIDEO_STYLES.keys()))
    scr.add_argument('--duration', '-d', type=int, default=3)

    # shoot
    sht = sub.add_parser('shoot', help='生成拍摄指南')
    sht.add_argument('--topic', '-t', required=True)
    sht.add_argument('--style', '-s', default='cognitive', choices=list(VIDEO_STYLES.keys()))
    sht.add_argument('--duration', '-d', type=int, default=3)

    # teleprompter
    tel = sub.add_parser('teleprompter', help='生成提词器')
    tel.add_argument('--topic', '-t', required=True)
    tel.add_argument('--style', '-s', default='cognitive', choices=list(VIDEO_STYLES.keys()))
    tel.add_argument('--duration', '-d', type=int, default=3)

    # topics
    top = sub.add_parser('topics', help='生成选题队列')
    top.add_argument('--niche', '-n', default='AI/一人公司')
    top.add_argument('--count', '-c', type=int, default=10)

    # adapt
    adp = sub.add_parser('adapt', help='多平台适配')
    adp.add_argument('--topic', '-t', required=True)
    adp.add_argument('--style', '-s', default='cognitive')
    adp.add_argument('--duration', '-d', type=int, default=3)
    adp.add_argument('--platforms', '-p', default='weishi,xhs,douyin')

    # analyze
    ana = sub.add_parser('analyze', help='分析脚本质量')
    ana.add_argument('--text', help='脚本文本')
    ana.add_argument('--file', '-f', help='脚本文件路径')

    # styles
    sub.add_parser('styles', help='列出视频风格')

    # platforms
    sub.add_parser('platforms', help='列出平台规格')

    args = parser.parse_args()

    if args.api:
        input_data = json.loads(sys.stdin.read())
        result = handle_api(input_data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.command:
        parser.print_help()
        print(f"\n📌 版本: {VERSION}")
        print("\n示例:")
        print('  python3 video_producer.py pipeline --topic "AI员工体系" --style cognitive --duration 3')
        print('  python3 video_producer.py script --topic "一人公司" --style story')
        print('  python3 video_producer.py topics --niche "AI/一人公司" --count 10')
        print('  python3 video_producer.py analyze --file my_script.md')
        print('  echo \'{"action":"pipeline","topic":"test"}\' | python3 video_producer.py --api')
        return

    if args.command == 'pipeline':
        result = handle_api({"action": "pipeline", "topic": args.topic,
                             "style": args.style, "duration": args.duration,
                             "platforms": args.platforms.split(',')})
    elif args.command == 'script':
        result = handle_api({"action": "script", "topic": args.topic,
                             "style": args.style, "duration": args.duration})
    elif args.command == 'shoot':
        result = handle_api({"action": "shooting_guide", "topic": args.topic,
                             "style": args.style, "duration": args.duration})
    elif args.command == 'teleprompter':
        result = handle_api({"action": "teleprompter", "topic": args.topic,
                             "style": args.style, "duration": args.duration})
    elif args.command == 'topics':
        result = handle_api({"action": "topics", "niche": args.niche, "count": args.count})
    elif args.command == 'adapt':
        result = handle_api({"action": "adapt", "topic": args.topic,
                             "style": args.style, "duration": args.duration,
                             "platforms": args.platforms.split(',')})
    elif args.command == 'analyze':
        text = getattr(args, 'text', None)
        if hasattr(args, 'file') and args.file:
            text = Path(args.file).read_text()
        result = handle_api({"action": "analyze", "text": text or ""})
    elif args.command == 'styles':
        result = handle_api({"action": "styles"})
    elif args.command == 'platforms':
        result = handle_api({"action": "platforms"})
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
