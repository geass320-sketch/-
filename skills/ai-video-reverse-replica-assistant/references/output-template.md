# 原生优先视频逆向报告（模板）

## 1. 原生镜头解析（必有）
| sequence_id | timestamp | cut_type | shot_scale | camera_movement | continuity_logic | visual_description | micro_motion | sfx_layer | emotion_pulse |
|---|---|---|---|---|---|---|---|---|---|

## 2. 连续性与节奏诊断（必有）
- 剪辑点策略：
- 动作接点：
- 视线逻辑：
- 空间转换：
- 节奏脉冲：

## 3. 角色设定表
| 角色代号 | 外观 | 服装 | 性格 | 角色提示词(EN) | 一致性关键词 |
|---|---|---|---|---|---|

## 4. 生成提示词与执行参数（Dreamina）
- dreamina_prompt:
- camera_parameters: horizontal / vertical / zoom / stability

## 5. 四宫格导出（可选）
| source_sequence_id | panel_1_start | panel_2_motion | panel_3_turn | panel_4_lock |
|---|---|---|---|---|

## 6. JSON结果
```json
{
  "native_analysis": {"sequences": []},
  "four_panel_export": {"enabled": true, "panel_units": []},
  "generation_package": {
    "dreamina_prompt": "",
    "camera_parameters": {
      "horizontal": 0,
      "vertical": 0,
      "zoom": 0,
      "stability": "medium"
    }
  }
}
```
