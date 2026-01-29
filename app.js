const storyTitle = document.getElementById("story-title");
const storyText = document.getElementById("story-text");
const generateBtn = document.getElementById("generate-btn");
const shuffleBtn = document.getElementById("shuffle-btn");
const downloadBtn = document.getElementById("download-btn");
const storyboardGrid = document.getElementById("storyboard-grid");
const panelCount = document.getElementById("panel-count");
const canvas = document.getElementById("storyboard-canvas");
const ctx = canvas.getContext("2d");

const PANEL_TOTAL = 25;
const GRID_SIZE = 5;
const PANEL_SIZE = canvas.width / GRID_SIZE;
const SAMPLE_STORIES = [
  "雾气笼罩的海岸，小镇灯塔突然熄灭。少年决定出海寻找失联的父亲，在海怪、迷雾与旧日传说之间穿行。最终他在风暴中心点亮了灯塔，也找回了家族的守护使命。",
  "旧城的雨夜，记者追踪一宗失踪案。她发现案件与一座废弃剧院有关，舞台上隐藏着从未公开的证据。幕后凶手被揭开，剧院重现灯光。",
  "在未来的浮空城市，快递员意外收到一枚来自过去的怀表。怀表引导他穿梭不同街区，重组记忆碎片，揭露城市能源即将崩溃的真相。"
];

function splitStory(text) {
  const sentences = text
    .split(/(?<=[。！？!?\.])|\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (sentences.length === 0) {
    return ["请填写故事内容，再生成分镜。"];
  }
  return sentences;
}

function padPanels(sentences) {
  const panels = [];
  let index = 0;
  while (panels.length < PANEL_TOTAL) {
    panels.push(sentences[index % sentences.length]);
    index += 1;
  }
  return panels.slice(0, PANEL_TOTAL);
}

function hashColor(text) {
  let hash = 0;
  for (let i = 0; i < text.length; i += 1) {
    hash = text.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 65%, 45%)`;
}

function renderGrid(panels) {
  storyboardGrid.innerHTML = "";
  panels.forEach((panel, idx) => {
    const card = document.createElement("div");
    card.className = "story-card";
    card.style.background = hashColor(panel + idx);
    const label = document.createElement("span");
    label.textContent = `镜头 ${idx + 1}`;
    const text = document.createElement("p");
    text.textContent = panel;
    card.append(label, text);
    storyboardGrid.append(card);
  });
  panelCount.textContent = `共 ${panels.length} 格`;
}

function wrapText(text, x, y, maxWidth, lineHeight) {
  const words = text.split("");
  let line = "";
  const lines = [];

  words.forEach((word) => {
    const testLine = line + word;
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && line !== "") {
      lines.push(line);
      line = word;
    } else {
      line = testLine;
    }
  });
  if (line) {
    lines.push(line);
  }

  lines.forEach((lineText, index) => {
    ctx.fillText(lineText, x, y + index * lineHeight);
  });
}

function renderCanvas(panels, title) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.font = "32px 'Inter', 'PingFang SC', sans-serif";
  ctx.fillStyle = "#111827";
  ctx.fillText(title || "故事分镜", 40, 50);

  panels.forEach((panel, idx) => {
    const row = Math.floor(idx / GRID_SIZE);
    const col = idx % GRID_SIZE;
    const x = col * PANEL_SIZE;
    const y = row * PANEL_SIZE + 80;
    const padding = 20;

    ctx.fillStyle = hashColor(panel + idx);
    ctx.fillRect(x + 10, y + 10, PANEL_SIZE - 20, PANEL_SIZE - 20);

    ctx.fillStyle = "rgba(255,255,255,0.95)";
    ctx.fillRect(x + 20, y + 20, PANEL_SIZE - 40, PANEL_SIZE - 40);

    ctx.fillStyle = "#1f2937";
    ctx.font = "20px 'Inter', 'PingFang SC', sans-serif";
    ctx.fillText(`镜头 ${idx + 1}`, x + padding + 6, y + padding + 24);

    ctx.fillStyle = "#374151";
    ctx.font = "18px 'Inter', 'PingFang SC', sans-serif";
    wrapText(panel, x + padding + 6, y + padding + 52, PANEL_SIZE - 2 * padding - 12, 22);
  });
}

function generateStoryboard() {
  const text = storyText.value.trim();
  const sentences = splitStory(text);
  const panels = padPanels(sentences);
  renderGrid(panels);
  renderCanvas(panels, storyTitle.value.trim());
  downloadBtn.disabled = false;
}

function applySampleStory() {
  const sample = SAMPLE_STORIES[Math.floor(Math.random() * SAMPLE_STORIES.length)];
  storyText.value = sample;
}

function downloadImage() {
  const link = document.createElement("a");
  const title = storyTitle.value.trim() || "storyboard";
  link.download = `${title}-storyboard.png`;
  link.href = canvas.toDataURL("image/png");
  link.click();
}

shuffleBtn.addEventListener("click", () => {
  applySampleStory();
  generateStoryboard();
});

generateBtn.addEventListener("click", generateStoryboard);

downloadBtn.addEventListener("click", downloadImage);

applySampleStory();
renderGrid(padPanels(splitStory(storyText.value)));
renderCanvas(padPanels(splitStory(storyText.value)), "故事分镜");
