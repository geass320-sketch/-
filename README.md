# Seedance Automation Pipeline

## 目标

本仓库提供 Jimeng / Seedance 自动化生成流水线，重点保证：
- 可跑通（点击生成必须有可证明触发）
- 不误下载（只下载本次新卡片）
- 续写不重拍（中文连续性约束）

## 运行

```bash
python auto_gen.py \
  --base-url "https://seedance.example.com/create" \
  --cookies ./cookies.json \
  --prompt "雨夜街头，角色继续向前奔跑，镜头稳定跟拍" \
  --model "Seedance 2.0" \
  --ratio "16:9" \
  --duration "5s" \
  --mode text2video \
  --output-dir ./downloads
```

可选素材输入：
- `--reference-path /local/ref1.jpg`（可多次传）
- `--reference-url https://.../ref1.jpg`（可多次传，会自动下载到 `temp/` 后上传）

续写相关：
- `--first-frame ./assets/frame0.png`
- `--last-frame ./assets/frame1.png`
- `--end-state "角色停在门前回头"`

## Selector 自检步骤（必须）

程序会在点生成前执行 `preflight_selectors()`：
- prompt/model/ratio/duration/generate 要求 `count==1`
- mode/upload_input/latest_video 要求 `count>=1` 且可见
- 任一失败直接抛 `PreflightError`，绝不点生成

快速自检：
1. 正常跑一遍，确认 preflight 通过；
2. 故意改错 `generate_button`，应在 preflight 阶段失败；
3. 恢复后再跑正式任务。

快速自检命令（只做选择器探测，不触发生成）：

```bash
python auto_gen.py \
  --base-url "https://seedance.example.com/create" \
  --cookies ./cookies.json \
  --prompt "selector-check" \
  --model "Seedance 2.0" \
  --ratio "16:9" \
  --duration "5s" \
  --selector-self-check
```

日志会输出 `preflight_report`，包含每个候选 selector 的 count/visible，可直接定位是哪个失效。

## 全能参考模式说明

- 全能参考 **不强制上传图片**。
- 当未提供任何素材时，允许纯文本直接生成。
- 只有你提供了 `reference-path/reference-url` 或首尾帧但上传失败时，才报：
  - “当前缺少可上传的本地文件路径/素材下载失败”。

## 触发成功判定（防“看起来点了但没生效”）

点击生成后 5~8 秒内必须命中任一条件：
- 出现“生成中/排队中/处理中”toast
- 卡片数增加
- 生成按钮进入 busy/loading

否则执行一次纠错重试（滚动到按钮 + 关闭遮挡层 + 再点一次），仍失败则报错并附带诊断信息。

## 完成判定与下载（防旧视频 / 00:00）

完成判定必须同时满足：
- `new_src` 非 loading pattern 且 `new_src != old_src`
- `video.duration >= 3s`
- `videoWidth/videoHeight >= 200`
- UI 不为 `00:00` 占位

下载必须绑定 `new_src` 对应卡片作用域，不使用全局下载按钮。
`expect_download()` 不触发时，回退到真实视频 URL 直链下载。

## 运行日志

每任务会记录：
- `plan_id`
- `mode_ui/mode_req`
- `upload_ok`
- `prompt_len`
- `old_src/new_src`
- `old_card_count/new_card_count`
- `toast/form_errors`
- `generate_button_visible` 与 `visible_bottom_actions`（会输出当前可见按钮清单，如 `Button#4: 回到底部` / `Button#2: (空)`）
- `upload_state`（上传缩略图计数 + file input 已写入数量）
- 下载后的 `ffprobe` 摘要


## 失败提示判定说明

脚本只会基于页面上**实际抓到的提示文本**报告失败原因（toast/表单红字/结果卡片文本）。
- 如果抓到如“审核未通过/生成失败/网络异常”等明确文案，会原样输出。
- 如果未抓到明确失败提示，不会臆测原因，会提示“页面未检测到明确失败提示”。


## 上传 / 模型 / 生成按钮卡住的排查

最新逻辑已做以下兜底：
- 上传：只通过 `input[type=file].set_input_files()` 直写文件，不点击上传按钮，避免弹出系统文件选择框阻塞。

- 模式：脚本会先按 `--mode` 主动点击模式 Tab（不是只读当前模式），失败会直接报“模式选择失败”。
- 模型/时长：带 3 次重试，失败会自动 `Escape` 收起层后重选。
- 生成：先检查按钮禁用态，再滚动、关遮挡层、强制点击、回车兜底。

如果仍卡住，请先跑 `--selector-self-check`，并贴出 `preflight_report` 与 `diagnostics`。
