# 故事 5×5 分镜生成器

这是一个纯静态的前端应用，用于把故事文本拆解成 25 格分镜，并导出 PNG 画布。

## 本地运行

```bash
python -m http.server 8000
```

浏览器访问 `http://127.0.0.1:8000/index.html`。

## 打包前端应用

使用内置脚本把静态文件打包成 zip：

```bash
./package.sh
```

输出路径：`dist/storyboard-app.zip`。
