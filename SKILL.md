---
name: video-producer
description: Full-pipeline video production for short-form content creators. Generates PREP-structured scripts, shot lists, teleprompter text, topic queues with scoring, and multi-platform adaptation (视频号/小红书/抖音/YouTube/X). 6 video styles (cognitive/tutorial/case_study/story/comparison/list). Use when creating video content, planning video topics, generating shooting guides, adapting scripts for multiple platforms, or analyzing existing video scripts. Supports bilingual (zh/en) output and SkillPay billing.
---

# Video Producer v1.0

Full-pipeline video production: topic → script → shooting guide → teleprompter → multi-platform publish.
Built on the PREP persuasion framework (Point→Reason→Example→Point) adapted for video.

## Quick Start

### Full Pipeline (one command → all deliverables)
```bash
python3 scripts/video_producer.py pipeline --topic "AI员工体系" --style cognitive --duration 3
```

### Individual Steps
```bash
# Script only
python3 scripts/video_producer.py script --topic "一人公司" --style cognitive --duration 3

# Shooting guide (shot list + checklist)
python3 scripts/video_producer.py shoot --topic "一人公司" --style cognitive --duration 3

# Teleprompter (plain text for recording)
python3 scripts/video_producer.py teleprompter --topic "一人公司" --style cognitive

# Topic queue (scored + scheduled)
python3 scripts/video_producer.py topics --niche "AI/一人公司" --count 10

# Multi-platform adaptation
python3 scripts/video_producer.py adapt --topic "一人公司" --platforms weishi,xhs,douyin,youtube

# Analyze existing script
python3 scripts/video_producer.py analyze --file my_script.md

# List styles / platforms
python3 scripts/video_producer.py styles
python3 scripts/video_producer.py platforms
```

### API Mode (JSON in/out)
```bash
echo '{"action":"pipeline","topic":"AI员工","style":"cognitive","duration":3}' | python3 scripts/video_producer.py --api
```

## Video Styles (6)

| Style | Name | Best For |
|-------|------|----------|
| `cognitive` | 认知型 | Concept explanation, trend analysis, new tools |
| `tutorial` | 教程型 | Step-by-step guides, how-to |
| `case_study` | 案例型 | Product demos, real data, reviews |
| `story` | 故事型 | Personal brand, transformation, emotions |
| `comparison` | 对比型 | A vs B, tool/strategy comparisons |
| `list` | 清单型 | Tool recommendations, must-know lists |

## Platforms (5)

| Platform | ID | Best Duration |
|----------|----|---------------|
| 视频号 | `weishi` | 3-5 min |
| 小红书 | `xhs` | 2-3 min |
| 抖音 | `douyin` | 1-3 min |
| YouTube | `youtube` | 8-15 min |
| X/Twitter | `x` | 30-60s |

## Pipeline Output

`pipeline` action generates all deliverables in one call:

1. **Script** — PREP-structured outline with time allocation, hooks, visual suggestions, production notes
2. **Shooting Guide** — Shot list table, equipment checklist, recording tips, time estimates
3. **Teleprompter** — Plain text sections for on-camera reading
4. **Platform Adaptation** — Titles, descriptions, tags, cover tips, publish order per platform

## PREP Framework for Video

See `references/prep-video-framework.md` for the complete framework including time allocation ratios per style, 12 topic logics, and scoring criteria.

See `references/platform-specs.md` for detailed platform specifications.

## API Actions

| Action | Description | Paid |
|--------|-------------|------|
| `pipeline` | Full pipeline (all deliverables) | $1.00 |
| `script` | Script generation only | $0.50 |
| `shooting_guide` | Shot list + checklist | $0.50 |
| `teleprompter` | Plain text teleprompter | Free |
| `topics` | Topic queue with scoring | $0.50 |
| `adapt` | Multi-platform adaptation | $0.50 |
| `analyze` | Script quality analysis | $0.50 |
| `styles` | List video styles | Free |
| `platforms` | List platform specs | Free |

## Script Analysis Scoring

| Component | Max | What it measures |
|-----------|-----|-----------------|
| Hook | 25 | Opening attention grab |
| Reason | 20 | Motivation/pain point |
| Example | 35 | Core content richness |
| CTA | 20 | Close + call to action |

Grades: S(85+) / A(70+) / B(50+) / C(35+) / D(<35)

## Files

- `scripts/video_producer.py` — Main generator
- `scripts/skillpay.py` — SkillPay billing integration
- `scripts/config.json` — Skill configuration
- `references/prep-video-framework.md` — PREP video framework details
- `references/platform-specs.md` — Platform specifications
