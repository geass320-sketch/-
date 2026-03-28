# lanshu-waytovideo 项目分析（面向即梦网页版迁移）

目标仓库：`https://github.com/cclank/lanshu-waytovideo/tree/main`

## 1. 原项目定位

该项目核心是一个基于 Playwright 的网页自动化视频生成 Skill，重点场景包括：
- 文生视频（T2V）
- 图生视频（I2V）
- 参考视频生成（V2V）
- 自动下载成片

## 2. 可迁移的核心架构

适合复用到即梦网页版的能力：
1. **浏览器会话复用 + 登录态注入**
2. **参数化生成（模型、比例、时长、Prompt）**
3. **轮询生成状态并下载**
4. **对生成结果进行自动校验（时长/分辨率/src 变化）**

## 3. 即梦迁移中的真实阻塞点（已归纳）

1. 上传接口不是“纯 input[type=file]”路径，前端有事件链路校验。
2. 登录态可能主要在 localStorage/token，不是 cookies。
3. CDP 新 context 与用户真实 Chrome profile 隔离，无法直接继承个人登录态。
4. 运行环境沙盒浏览器通常只有空白 tab，且与用户本地浏览器隔离。

## 4. 当前代码已做的适配

- 增加认证多通道：`storage_state` / `localStorage JSON` / cookies。
- 上传采用双策略：`set_input_files + 事件`，失败后回退 `expect_file_chooser`。
- 保留旧 planner 命名兼容别名，减少调用方改造成本。

## 5. 下一步建议

1. 在真实即梦页面录制 Playwright trace，固化稳定 selector（上传按钮、上传完成标记）。
2. 增加“登录态探针”逻辑（检查关键 localStorage key 是否存在）。
3. 下载链路补充 fallback：按钮下载失败时转资源链接抓取。
