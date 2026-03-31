# AI 视频反推与复刻报告（融合模板）

## 任务模式
- replicate | variation | enhance

## 假设条件
- 

## 输入映射结果
```json
{
  "video_input": {"type": "file | url", "value": ""},
  "user_intent": {"mode": "replicate", "description": ""},
  "edit_instruction": {
    "scene": null,
    "character": null,
    "style": null,
    "action": null,
    "emotion": null
  }
}
```

## 1. 角色设定表
| 角色代号 | 角色类型 | 身份定位 | 外貌特征 | 服装风格 | 性格标签 | 角色设定图提示词(EN) | 一致性关键词 |
|---|---|---|---|---|---|---|---|
| {角色A} |  |  |  |  |  |  |  |

## 2. 完整分镜表
| 镜号 | 时间 | 时长 | 出镜角色 | 画面内容 | 画面提示词(EN) | 文案/台词 | 镜头类型 | 功能 |
|---|---|---|---|---|---|---|---|---|
| 1 | 00:00 | 2s | {角色A} |  |  |  | 中景 | 钩子 |

## 3. 结构拆解
- 整体结构：
- 钩子设计：
- 节奏分析：
- 视觉风格：

## 4. 元提示词模板
```text
{角色} in {场景}, {动作}, {构图}, {光影}, {风格词}, {质量词}
```

## 5. 验证测试（关键词）
- 测试1（角色替换）：
- 测试2（场景替换）：
- 测试3（风格替换）：

## 6. 提示词替换指南
- 可替换字段：角色 / 场景 / 动作 / 构图 / 光影 / 风格 / 质量
- 替换原则：先锁定角色一致性关键词，再替换场景与动作，最后微调风格词强度。

## JSON结果
```json
{
  "analysis_report": {"shots": []},
  "character_sheet": [],
  "script_reconstruction": {"scenes": []},
  "story_structure": {
    "setup": "",
    "conflict": "",
    "turning_point": "",
    "climax": "",
    "resolution": "",
    "emotion_curve": ["calm", "tension", "peak", "release"]
  },
  "optimized_script": {
    "modifications_applied": [],
    "logic_check": {"status": "valid", "notes": ""},
    "updated_scenes": []
  },
  "meta_prompts": [],
  "replacement_guide": [],
  "generation_package": {
    "dreamina_prompt": "",
    "camera_parameters": {
      "horizontal": 0,
      "vertical": 0,
      "zoom": 0,
      "stability": "medium"
    },
    "character_ref": {
      "appearance": "",
      "costume": "",
      "identity_tags": [],
      "consistency_rules": []
    },
    "frame_guidance": {
      "start_frame": "",
      "end_frame": "",
      "transition_hint": ""
    }
  }
}
```
