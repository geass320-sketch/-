---
name: ai-video-reverse-replica-assistant
description: Perform native cut-based reverse analysis for videos as the primary engineering layer, then optionally compress native shot groups into a four-panel structure for generation, storyboard display, or model-friendly execution.
---

# AI 视频反推与复刻助手（原生优先版）

核心原则：
- **第一层（工程层）必须是原生 Cut-based 分析**。
- **第二层（执行层）才是四宫格压缩导出**（可选）。

> 一句话：要看懂视频，用原生；要驱动模型，在原生基础上转四宫格。

## 1) 输入协议（Input Schema）

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
  "analysis_preference": {
    "core_layer": "native_only | native_plus_four_panel",
    "need_four_panel_export": true
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

默认策略：`core_layer = native_plus_four_panel`。

## 2) 双层工作流

### A. 原生镜头解析器（必做）

必须按真实剪辑逻辑拆解：
- 按剪辑点切分（hard cut / dissolve / wipe 等）
- 按叙事断点分组（sequence）
- 保留 continuity logic（视线、运动方向、空间连续）
- 标注：镜头运动、景别、情绪转折、物理微动态、拟音层

推荐输出粒度：`timestamp` 精确到 0.1s。

### B. 四宫格压缩器（可选）

仅当需要生成/展示时调用：
- 起始状态
- 运动展开
- 视觉转折
- 收束定格

用途：
- 图生视频执行
- storyboard 可视化
- 模型稳定节奏骨架

## 3) 为什么原生优先（执行约束）

四宫格不得替代原生层，原因：
1. 四宫格会抹平真实节奏（丢失切点原因）。
2. 四宫格会误伤长镜头重心（前铺垫后爆点被均匀化）。
3. 四宫格更像生成模板，不是分析模板。

## 4) 原生层输出结构（核心）

```json
{
  "native_analysis": {
    "sequences": [
      {
        "sequence_id": "S01",
        "narrative_function": "setup | conflict | turning_point | climax | resolution",
        "shots": [
          {
            "timestamp": "00:00-00:03.2",
            "cut_type": "hard_cut",
            "shot_scale": "medium close-up",
            "camera_movement": "slow push-in",
            "continuity_logic": "eyeline_match",
            "visual_description": "人物侧脸站在窗边，暖色逆光，发丝轻微飘动，胸腔呼吸可见",
            "micro_motion": ["hair drift", "breathing", "fabric ripple"],
            "sfx_layer": ["room tone", "distant traffic", "soft cloth friction"],
            "emotion_pulse": "calm -> tension"
          }
        ]
      }
    ]
  }
}
```

## 5) 四宫格导出结构（可选）

```json
{
  "four_panel_export": {
    "enabled": true,
    "panel_units": [
      {
        "source_sequence_id": "S01",
        "panel_1_start": "起始状态",
        "panel_2_motion": "运动展开",
        "panel_3_turn": "视觉转折",
        "panel_4_lock": "收束定格"
      }
    ]
  }
}
```

## 6) 报告交付（Markdown）

固定章节：
1. 原生镜头解析（必有）
2. 连续性与节奏诊断（必有）
3. 角色设定表（可用于生成）
4. 生成提示词与执行参数（Dreamina）
5. 四宫格导出（仅在 enabled=true 时）
6. JSON结果

## 7) OpenClaw 上传包

打包命令：

```bash
python3 skills/ai-video-reverse-replica-assistant/scripts/package_openclaw_skill.py
```

产物（本地生成，不提交仓库）：
- `skills/ai-video-reverse-replica-assistant/assets/openclaw-skill-ai-video-reverse-replica-assistant.zip`
