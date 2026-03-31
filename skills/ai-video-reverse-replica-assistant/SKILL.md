---
name: ai-video-reverse-replica-assistant
description: Produce a dual-format (human-readable + machine-parseable) storyboard reverse-analysis package from videos, combining character sheets, shot tables, narrative/rhythm analysis, rewrite logic, and Dreamina-ready execution prompts/parameters. Use for replicate/variation/enhance tasks from video file or URL.
---

# AI 视频反推与复刻助手（融合增强版）

融合目标：同时满足“创作可读性”与“工程可执行性”。

## 1) 核心能力

1. 视频内容分析：角色、场景、动作、对白、镜头语言。
2. 分镜逆向报告：角色设定表 + 完整分镜表 + 结构拆解。
3. 叙事重构与改写：支持变量替换与逻辑联动修正。
4. Prompt 工程化导出：元提示词 + Dreamina 执行包。
5. 双格式输出：Markdown 报告 + 严格 JSON Schema 结果。

## 2) 输入协议（Input Schema）

```json
{
  "video_input": {
    "type": "file | url",
    "value": "string"
  },
  "user_intent": {
    "mode": "replicate | variation | enhance",
    "description": "string"
  },
  "edit_instruction": {
    "scene": "string",
    "character": "string",
    "style": "string",
    "action": "string",
    "emotion": "string"
  }
}
```

约束：
- 必填：`video_input`、`user_intent.mode`。
- 缺失字段置 `null` 并在“假设条件”说明。
- 角色占位符统一用 `{角色A}`、`{角色B}`。
- 时间精确到秒。

## 3) 工作流引擎

1. 输入视频并完成输入映射。
2. 镜头拆解（画面、构图、运镜、情绪）。
3. 剧本还原与故事结构分析。
4. 若有修改：执行变量替换 -> 逻辑校验 -> 全量重构。
5. 生成元提示词与 Dreamina 执行包。
6. 输出 Markdown 六章节 + JSON 结构结果。

## 4) 子 Agent 分工

- Shot Analyzer：镜头切分与画面字段提取。
- Motion Tracker：运镜类型/方向/强度识别。
- Narrative Engine：剧本还原、节拍与情绪曲线。
- Rewrite Engine：改写请求联动修正与一致性检查。
- Prompt Generator：分镜提示词、Cref、运镜参数生成。

## 5) 强制输出章节（Markdown）

必须按顺序输出以下 6 章：

1. 角色设定表
2. 完整分镜表
3. 结构拆解
4. 元提示词模板
5. 验证测试（关键词）
6. 提示词替换指南

## 6) 角色设定表规范

每个角色需包含：
- 基础信息：角色类型、身份定位、外貌特征、服装风格、性格标签
- 角色设定图提示词（英文）
- 一致性关键词（简化关键词）

角色设定图提示词结构：
`[identity], [appearance], [costume], [pose], full body, character design sheet, white background, multiple views, [style], high quality`

一致性关键词结构：
`[core traits], [costume traits], [expression/temperament], [style]`

## 7) 完整分镜表规范

字段固定：

| 镜号 | 时间 | 时长 | 出镜角色 | 画面内容 | 画面提示词(EN) | 文案/台词 | 镜头类型 | 功能 |
|---|---|---|---|---|---|---|---|---|

规则：
- 镜头类型：大远景、远景、中景、近景、特写。
- 功能标签：铺垫、钩子、冲突、高潮、收束。
- 画面提示词结构：`{角色}, [action], [scene], [composition], [lighting], [style]`。

## 8) 结构拆解规范

至少覆盖：
1. 整体结构（阶段 + 镜号范围）
2. 钩子设计（类型/话术/视觉抓手）
3. 节奏分析（平均镜头时长/节奏变化点）
4. 视觉风格（配色/质感/推荐风格词）

## 9) 元提示词与风格词

元提示词模板：
`{角色} in {场景}, {动作}, {构图}, {光影}, {风格词}, {质量词}`

通用风格词：
- cinematic lighting
- high contrast
- atmospheric perspective
- film grain
- epic scale

通用质量词：
- high quality
- detailed
- professional
- photorealistic
- 8k

## 10) 机器可解析输出（Output Schema）

Markdown 之后追加 JSON，结构如下：

```json
{
  "analysis_report": {
    "shots": [
      {
        "shot_id": "string",
        "duration": "number",
        "scene": "string",
        "subject": "string",
        "composition": {
          "shot_size": "wide | medium | close | extreme_close",
          "angle": "eye_level | low | high | tilt",
          "framing": "center | rule_of_thirds | symmetry"
        },
        "camera_motion": {
          "type": "push | pull | pan | tilt | track | handheld",
          "direction": "horizontal | vertical | forward | circular",
          "intensity": "1-10"
        },
        "lighting": "string",
        "color": "string",
        "mood": "string",
        "prompt": "string"
      }
    ]
  },
  "character_sheet": [],
  "script_reconstruction": {
    "scenes": []
  },
  "story_structure": {
    "setup": "string",
    "conflict": "string",
    "turning_point": "string",
    "climax": "string",
    "resolution": "string",
    "emotion_curve": ["calm", "tension", "peak", "release"]
  },
  "optimized_script": {
    "modifications_applied": [],
    "logic_check": {
      "status": "valid | adjusted",
      "notes": "string"
    },
    "updated_scenes": []
  },
  "meta_prompts": [],
  "replacement_guide": [],
  "generation_package": {
    "dreamina_prompt": "string",
    "camera_parameters": {
      "horizontal": "number",
      "vertical": "number",
      "zoom": "number",
      "stability": "low | medium | high"
    },
    "character_ref": {
      "appearance": "string",
      "costume": "string",
      "identity_tags": ["string"],
      "consistency_rules": ["string"]
    },
    "frame_guidance": {
      "start_frame": "string",
      "end_frame": "string",
      "transition_hint": "string"
    }
  }
}
```

## 11) NFR 与验收标准

NFR 目标：
- 结构化可读性：100%
- 同输入偏差：<5%
- 角色漂移率：<10%
- 短视频分析时延：<10s（视模型与环境）

验收清单：
- [ ] 六章节齐全
- [ ] 角色图提示词全部英文
- [ ] 分镜表含时间/时长/镜头类型/功能
- [ ] 结构拆解包含结构+钩子+节奏+风格
- [ ] 有元提示词与关键词验证测试
- [ ] 有替换指南与 JSON 结果
- [ ] 若有改写，逻辑检查结果已给出

未达标时必须输出：失败项、原因、补救动作。


## 12) 分镜 Excel 导出

使用内置脚本生成可交付 Excel 与预览图：

```bash
python3 skills/ai-video-reverse-replica-assistant/scripts/generate_storyboard_excel.py
```

输出文件（本地生成，不提交二进制产物）：
- `skills/ai-video-reverse-replica-assistant/assets/storyboard-example.xlsx`
- `skills/ai-video-reverse-replica-assistant/assets/storyboard-example-preview.svg`



## 13) OpenClaw 上传包

将技能打包为 OpenClaw 可上传 zip：

```bash
python3 skills/ai-video-reverse-replica-assistant/scripts/package_openclaw_skill.py
```

产物（本地生成，不提交仓库）：
- `skills/ai-video-reverse-replica-assistant/assets/openclaw-skill-ai-video-reverse-replica-assistant.zip`

zip 包含：
- `openclaw/skill.yaml`
- `openclaw/system_prompt.md`
- `openclaw/output_schema.json`
- `openclaw/examples/request.json`
