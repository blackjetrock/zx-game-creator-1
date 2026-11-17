/**
 * ZX Spectrum Game Creator Studio - Frontend Application Logic
 * Full Visual IDE, Tile/Sprite/Room Editors, Z80 Code Generator, and Browser Simulator.
 */

// Spectrum 16 Color Palette (Normal + Bright)
const ZX_PALETTE = [
  "#000000", "#0000D7", "#D70000", "#D700D7", "#00D700", "#00D7D7", "#D7D700", "#D7D7D7",
  "#000000", "#0000FF", "#FF0000", "#FF00FF", "#00FF00", "#00FFFF", "#FFFF00", "#FFFFFF"
];

const COLOR_NAMES = ["Black", "Blue", "Red", "Magenta", "Green", "Cyan", "Yellow", "White"];

// Application State
let project = null;
let currentRoomIdx = 0;
let selectedTileId = 1;
let selectedSpriteId = "player";
let currentSpriteFrameIdx = 0;
let roomTool = "paint"; // "paint", "player", "enemy", "erase"
let spriteTool = "pencil";
let tileTool = "pencil";
let isDrawingRoom = false;
let isDrawingSprite = false;
let isDrawingTile = false;

// Audio Context for 1-Bit Beeper Simulation
let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return audioCtx;
}

// Sound Synthesizers (mimicking ZX Spectrum Port $FE beeper)
function playBeep(freq, duration, type = "square") {
  const chk = document.getElementById("sim-sound-chk");
  if (chk && !chk.checked) return;
  try {
    const ctx = getAudioContext();
    if (ctx.state === "suspended") ctx.resume();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (e) {}
}

function playSweep(startFreq, endFreq, duration) {
  const chk = document.getElementById("sim-sound-chk");
  if (chk && !chk.checked) return;
  try {
    const ctx = getAudioContext();
    if (ctx.state === "suspended") ctx.resume();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "square";
    osc.frequency.setValueAtTime(startFreq, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(endFreq, ctx.currentTime + duration);
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (e) {}
}

function playNoise(duration) {
  const chk = document.getElementById("sim-sound-chk");
  if (chk && !chk.checked) return;
  try {
    const ctx = getAudioContext();
    if (ctx.state === "suspended") ctx.resume();
    const bufferSize = ctx.sampleRate * duration;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }
    const noise = ctx.createBufferSource();
    noise.buffer = buffer;
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    noise.connect(gain);
    gain.connect(ctx.destination);
    noise.start();
  } catch (e) {}
}

// --- INITIALIZATION ---
window.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  setupColorSelects();
  setupHeaderButtons();
  setupRoomEditorEvents();
  setupSpriteEditorEvents();
  setupTileEditorEvents();
  setupSimulatorEvents();
  setupSettingsEvents();

  // Load default preset (Platformer)
  await loadPreset("platformer");
});

// Setup Color Dropdowns
function setupColorSelects() {
  const colorSelectIds = [
    "sprite-ink", "sprite-paper",
    "tile-ink", "tile-paper",
    "cfg-border", "cfg-paper", "cfg-ink"
  ];
  colorSelectIds.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = "";
    COLOR_NAMES.forEach((name, idx) => {
      const opt = document.createElement("option");
      opt.value = idx;
      opt.textContent = `${idx}: ${name}`;
      el.appendChild(opt);
    });
  });
}

// Tab Switching
function setupTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add("active");

      // Auto refresh views
      if (targetId === "tab-room") renderRoomCanvas();
      if (targetId === "tab-sprites") renderSpriteCanvas();
      if (targetId === "tab-tiles") renderTileCanvas();
      if (targetId === "tab-asm") fetchAssemblyCode();
      if (targetId === "tab-simulator") initSimulator();
    });
  });
}

// Preset Loader
async function loadPreset(type) {
  try {
    const res = await fetch(`/api/preset?type=${type}`);
    if (!res.ok) throw new Error("Failed to load preset");
    project = await res.json();
    currentRoomIdx = 0;
    updateAllViews();
  } catch (e) {
    console.error("Error loading preset:", e);
  }
}

function updateAllViews() {
  if (!project) return;
  updateSettingsForm();
  updateTilePalette();
  updateSpriteList();
  updateTileEditorList();
  updateRoomSelectors();
  renderRoomCanvas();
  renderSpriteCanvas();
  renderTileCanvas();
}

function setupHeaderButtons() {
  // Load preset button
  document.getElementById("btn-load-preset").addEventListener("click", () => {
    const sel = document.getElementById("preset-selector").value;
    loadPreset(sel);
  });

  // Switch tab to play in simulator
  document.getElementById("btn-test-play").addEventListener("click", () => {
    document.querySelector('.tab-btn[data-tab="tab-simulator"]').click();
    startSimulatorGame();
  });

  // Export .TAP
  document.getElementById("btn-export-tap").addEventListener("click", exportTapFile);
  document.getElementById("btn-download-tap-direct").addEventListener("click", exportTapFile);

  // Export .ASM
  document.getElementById("btn-export-asm").addEventListener("click", exportAsmFile);
  document.getElementById("btn-download-asm-direct").addEventListener("click", exportAsmFile);

  // Export .JSON
  document.getElementById("btn-export-json").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: "application/json" });
    const filename = `${project.config.title.toLowerCase().replace(/\s+/g, '_')}.json`;
    downloadBlob(blob, filename);
  });

  // Import .JSON
  document.getElementById("file-import-json").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        project = JSON.parse(event.target.result);
        currentRoomIdx = 0;
        updateAllViews();
        alert("Project loaded successfully!");
      } catch (err) {
        alert("Invalid project JSON: " + err.message);
      }
    };
    reader.readAsText(file);
  });

  // Copy Assembly
  document.getElementById("btn-copy-asm").addEventListener("click", () => {
    const text = document.getElementById("asm-code-area").value;
    navigator.clipboard.writeText(text).then(() => alert("Assembly code copied to clipboard!"));
  });

  document.getElementById("btn-refresh-asm").addEventListener("click", fetchAssemblyCode);
}

// Download Helper
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function exportTapFile() {
  try {
    const res = await fetch("/api/build/tap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "TAP compilation failed");
    }
    const blob = await res.blob();
    const safeName = project.config.title.replace(/[^a-zA-Z0-9_-]/g, "_").toLowerCase();
    downloadBlob(blob, `${safeName}.tap`);
  } catch (e) {
    alert("Error building TAP file: " + e.message);
  }
}

async function exportAsmFile() {
  try {
    const res = await fetch("/api/build/asm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project)
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.error);
    const blob = new Blob([data.asm], { type: "text/plain" });
    const safeName = project.config.title.replace(/[^a-zA-Z0-9_-]/g, "_").toLowerCase();
    downloadBlob(blob, `${safeName}.asm`);
  } catch (e) {
    alert("Error generating ASM: " + e.message);
  }
}

async function fetchAssemblyCode() {
  const area = document.getElementById("asm-code-area");
  const linesStat = document.getElementById("asm-lines-stat");
  const statusStat = document.getElementById("asm-status");
  statusStat.textContent = "Generating...";
  try {
    const res = await fetch("/api/build/asm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project)
    });
    const data = await res.json();
    if (data.success) {
      area.value = data.asm;
      linesStat.textContent = `Lines: ${data.lines}`;
      statusStat.textContent = "Generated OK";
    } else {
      area.value = "; Error generating assembly:\n; " + data.error;
      statusStat.textContent = "Error";
    }
  } catch (e) {
    area.value = "; Network error generating assembly: " + e.message;
    statusStat.textContent = "Network Error";
  }
}

// =============================================================================
// TAB 1: ROOM & LEVEL EDITOR
// =============================================================================
function setupRoomEditorEvents() {
  const canvas = document.getElementById("room-canvas");

  // Tool buttons
  const toolBtns = ["tool-paint", "tool-player", "tool-enemy", "tool-erase"];
  toolBtns.forEach(id => {
    document.getElementById(id).addEventListener("click", () => {
      toolBtns.forEach(b => document.getElementById(b).classList.remove("active"));
      document.getElementById(id).classList.add("active");
      roomTool = id.replace("tool-", "");
    });
  });

  // Canvas Mouse Events
  canvas.addEventListener("mousedown", (e) => {
    isDrawingRoom = true;
    handleRoomCanvasClick(e);
  });
  canvas.addEventListener("mousemove", (e) => {
    if (isDrawingRoom && (roomTool === "paint" || roomTool === "erase")) {
      handleRoomCanvasClick(e);
    }
  });
  window.addEventListener("mouseup", () => {
    isDrawingRoom = false;
  });

  // Room dropdown
  document.getElementById("room-select").addEventListener("change", (e) => {
    currentRoomIdx = parseInt(e.target.value);
    syncRoomFields();
    renderRoomCanvas();
  });

  // Add Room
  document.getElementById("btn-add-room").addEventListener("click", () => {
    const newId = project.rooms.length;
    // Copy empty grid (16 cols x 11 rows)
    const emptyGrid = Array.from({ length: 11 }, () => Array(16).fill(0));
    // Add solid floor and border by default
    for (let c = 0; c < 16; c++) {
      emptyGrid[0][c] = 1;
      emptyGrid[10][c] = 1;
    }
    for (let r = 0; r < 11; r++) {
      emptyGrid[r][0] = 1;
      emptyGrid[r][15] = 1;
    }
    project.rooms.push({
      id: newId,
      name: `Room ${newId + 1}`,
      width_tiles: 16,
      height_tiles: 11,
      tile_grid: emptyGrid,
      player_start: [2, 7],
      enemies: [],
      items: [],
      exits: { north: null, south: null, west: null, east: null },
      message: ""
    });
    currentRoomIdx = newId;
    updateRoomSelectors();
    renderRoomCanvas();
  });

  // Room Name
  document.getElementById("room-name-input").addEventListener("input", (e) => {
    if (project && project.rooms[currentRoomIdx]) {
      project.rooms[currentRoomIdx].name = e.target.value;
      updateRoomSelectors();
    }
  });

  // Exits
  ["north", "south", "west", "east"].forEach(dir => {
    document.getElementById(`exit-${dir}`).addEventListener("change", (e) => {
      const val = e.target.value === "none" ? null : parseInt(e.target.value);
      if (project && project.rooms[currentRoomIdx]) {
        project.rooms[currentRoomIdx].exits[dir] = val;
      }
    });
  });
}

function updateRoomSelectors() {
  const sel = document.getElementById("room-select");
  sel.innerHTML = "";
  project.rooms.forEach((r, idx) => {
    const opt = document.createElement("option");
    opt.value = idx;
    opt.textContent = `${idx}: ${r.name}`;
    sel.appendChild(opt);
  });
  sel.value = currentRoomIdx;

  // Update exit dropdowns
  ["north", "south", "west", "east"].forEach(dir => {
    const exSel = document.getElementById(`exit-${dir}`);
    exSel.innerHTML = '<option value="none">None</option>';
    project.rooms.forEach((r, idx) => {
      const opt = document.createElement("option");
      opt.value = idx;
      opt.textContent = `Room ${idx}: ${r.name}`;
      exSel.appendChild(opt);
    });
  });
  syncRoomFields();
}

function syncRoomFields() {
  const room = project.rooms[currentRoomIdx];
  if (!room) return;
  document.getElementById("room-name-input").value = room.name;
  ["north", "south", "west", "east"].forEach(dir => {
    const val = room.exits[dir];
    document.getElementById(`exit-${dir}`).value = val !== null && val !== undefined ? val : "none";
  });
}

function handleRoomCanvasClick(e) {
  const canvas = document.getElementById("room-canvas");
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = (e.clientX - rect.left) * scaleX;
  const y = (e.clientY - rect.top) * scaleY;

  // 16 cols x 11 rows -> each tile is (512 / 16) = 32px wide, (352 / 11) = 32px high
  const col = Math.floor(x / 32);
  const row = Math.floor(y / 32);
  if (col < 0 || col >= 16 || row < 0 || row >= 11) return;

  const room = project.rooms[currentRoomIdx];
  if (!room) return;

  if (roomTool === "paint") {
    room.tile_grid[row][col] = selectedTileId;
  } else if (roomTool === "erase") {
    room.tile_grid[row][col] = 0;
  } else if (roomTool === "player") {
    room.player_start = [col, row];
  } else if (roomTool === "enemy") {
    // Check if enemy exists here, if so remove, else add
    const existingIdx = room.enemies.findIndex(e => e.x === col && e.y === row);
    if (existingIdx >= 0) {
      room.enemies.splice(existingIdx, 1);
    } else {
      room.enemies.push({
        x: col,
        y: row,
        sprite_id: "enemy_bat",
        ai_type: "patrol_h",
        patrol_min: Math.max(0, col - 4),
        patrol_max: Math.min(15, col + 4),
        speed: 1,
        health: 1
      });
    }
  }
  renderRoomCanvas();
}

function renderRoomCanvas() {
  const canvas = document.getElementById("room-canvas");
  if (!canvas || !project) return;
  const ctx = canvas.getContext("2d");
  const room = project.rooms[currentRoomIdx];
  if (!room) return;

  // Clear background with Paper color
  const paperColor = ZX_PALETTE[project.config.paper_color] || "#000000";
  ctx.fillStyle = paperColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Render Tiles
  for (let r = 0; r < 11; r++) {
    for (let c = 0; c < 16; c++) {
      const tileId = room.tile_grid[r] ? room.tile_grid[r][c] : 0;
      drawTileToCanvas(ctx, tileId, c * 32, r * 32, 32, 32);
    }
  }

  // Draw Grid Lines (subtle)
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  for (let c = 0; c <= 16; c++) {
    ctx.beginPath();
    ctx.moveTo(c * 32, 0);
    ctx.lineTo(c * 32, 352);
    ctx.stroke();
  }
  for (let r = 0; r <= 11; r++) {
    ctx.beginPath();
    ctx.moveTo(0, r * 32);
    ctx.lineTo(512, r * 32);
    ctx.stroke();
  }

  // Draw Player Start Marker
  if (room.player_start) {
    const [px, py] = room.player_start;
    ctx.fillStyle = "rgba(0, 255, 255, 0.3)";
    ctx.fillRect(px * 32, py * 32, 32, 32);
    ctx.strokeStyle = "#00ffff";
    ctx.lineWidth = 2;
    ctx.strokeRect(px * 32, py * 32, 32, 32);
    // Draw Knight / Player Sprite preview
    drawSpriteToCanvas(ctx, "player", px * 32, py * 32, 32, 32);
  }

  // Draw Enemies
  room.enemies.forEach(e => {
    ctx.fillStyle = "rgba(255, 0, 0, 0.3)";
    ctx.fillRect(e.x * 32, e.y * 32, 32, 32);
    ctx.strokeStyle = "#ff0000";
    ctx.lineWidth = 2;
    ctx.strokeRect(e.x * 32, e.y * 32, 32, 32);
    drawSpriteToCanvas(ctx, e.sprite_id || "enemy_bat", e.x * 32, e.y * 32, 32, 32);
  });
}

function updateTilePalette() {
  const palette = document.getElementById("tile-palette");
  palette.innerHTML = "";
  Object.keys(project.tiles).forEach(tIdStr => {
    const tId = parseInt(tIdStr);
    const tile = project.tiles[tId];
    const item = document.createElement("div");
    item.className = `palette-item ${tId === selectedTileId ? "active" : ""}`;
    item.title = `${tile.name} (${tile.collision})`;

    const cvs = document.createElement("canvas");
    cvs.width = 32;
    cvs.height = 32;
    const ctx = cvs.getContext("2d");
    drawTileToCanvas(ctx, tId, 0, 0, 32, 32);

    item.appendChild(cvs);
    item.addEventListener("click", () => {
      selectedTileId = tId;
      document.querySelectorAll(".palette-item").forEach(p => p.classList.remove("active"));
      item.classList.add("active");
    });
    palette.appendChild(item);
  });
}

function drawTileToCanvas(ctx, tileId, x, y, w, h) {
  const tile = project.tiles[tileId];
  if (!tile || !tile.pixels || tile.pixels.length === 0) {
    // Empty
    ctx.fillStyle = "#000000";
    ctx.fillRect(x, y, w, h);
    return;
  }
  const brightOffset = tile.bright ? 8 : 0;
  const inkColor = ZX_PALETTE[tile.ink + brightOffset] || "#ffffff";
  const paperColor = ZX_PALETTE[tile.paper] || "#000000";

  ctx.fillStyle = paperColor;
  ctx.fillRect(x, y, w, h);

  ctx.fillStyle = inkColor;
  const pixelW = w / 16;
  const pixelH = h / 16;

  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      if (tile.pixels[r] && tile.pixels[r][c]) {
        ctx.fillRect(x + c * pixelW, y + r * pixelH, pixelW, pixelH);
      }
    }
  }
}

function drawSpriteToCanvas(ctx, spriteId, x, y, w, h) {
  const sprite = project.sprites[spriteId] || project.sprites["player"];
  if (!sprite || !sprite.frames || sprite.frames.length === 0) return;
  const frame = sprite.frames[0];
  const brightOffset = sprite.bright ? 8 : 0;
  const inkColor = ZX_PALETTE[sprite.ink + brightOffset] || "#ffff00";

  ctx.fillStyle = inkColor;
  const pixelW = w / 16;
  const pixelH = h / 16;

  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      if (frame[r] && frame[r][c]) {
        ctx.fillRect(x + c * pixelW, y + r * pixelH, pixelW, pixelH);
      }
    }
  }
}

// =============================================================================
// TAB 2: SPRITE EDITOR
// =============================================================================
function setupSpriteEditorEvents() {
  const canvas = document.getElementById("sprite-canvas");

  canvas.addEventListener("mousedown", (e) => {
    isDrawingSprite = true;
    handleSpritePixelClick(e);
  });
  canvas.addEventListener("mousemove", (e) => {
    if (isDrawingSprite && (spriteTool === "pencil" || spriteTool === "eraser")) {
      handleSpritePixelClick(e);
    }
  });
  window.addEventListener("mouseup", () => {
    isDrawingSprite = false;
  });

  // Tools
  const spTools = ["sp-tool-pencil", "sp-tool-eraser", "sp-tool-fill", "sp-tool-invert", "sp-tool-clear"];
  spTools.forEach(id => {
    document.getElementById(id).addEventListener("click", () => {
      spTools.forEach(b => document.getElementById(b).classList.remove("active"));
      document.getElementById(id).classList.add("active");
      spriteTool = id.replace("sp-tool-", "");
      if (spriteTool === "invert") invertSprite();
      if (spriteTool === "clear") clearSprite();
    });
  });

  // Color attributes
  document.getElementById("sprite-ink").addEventListener("change", (e) => {
    if (project.sprites[selectedSpriteId]) {
      project.sprites[selectedSpriteId].ink = parseInt(e.target.value);
      renderSpriteCanvas();
      renderRoomCanvas();
    }
  });
  document.getElementById("sprite-paper").addEventListener("change", (e) => {
    if (project.sprites[selectedSpriteId]) {
      project.sprites[selectedSpriteId].paper = parseInt(e.target.value);
      renderSpriteCanvas();
      renderRoomCanvas();
    }
  });
  document.getElementById("sprite-bright").addEventListener("change", (e) => {
    if (project.sprites[selectedSpriteId]) {
      project.sprites[selectedSpriteId].bright = e.target.checked;
      renderSpriteCanvas();
      renderRoomCanvas();
    }
  });

  // Frame navigation
  document.getElementById("btn-prev-frame").addEventListener("click", () => {
    const sp = project.sprites[selectedSpriteId];
    if (sp && sp.frames.length > 1) {
      currentSpriteFrameIdx = (currentSpriteFrameIdx - 1 + sp.frames.length) % sp.frames.length;
      updateFrameCounter();
      renderSpriteCanvas();
    }
  });
  document.getElementById("btn-next-frame").addEventListener("click", () => {
    const sp = project.sprites[selectedSpriteId];
    if (sp && sp.frames.length > 1) {
      currentSpriteFrameIdx = (currentSpriteFrameIdx + 1) % sp.frames.length;
      updateFrameCounter();
      renderSpriteCanvas();
    }
  });
  document.getElementById("btn-add-frame").addEventListener("click", () => {
    const sp = project.sprites[selectedSpriteId];
    if (sp) {
      // Clone current frame
      const current = sp.frames[currentSpriteFrameIdx] || Array.from({length: 16}, () => Array(16).fill(0));
      const clone = current.map(row => [...row]);
      sp.frames.push(clone);
      currentSpriteFrameIdx = sp.frames.length - 1;
      updateFrameCounter();
      renderSpriteCanvas();
    }
  });

  // Start Animation Loop for Preview
  setInterval(renderSpritePreview, 120);
}

function updateSpriteList() {
  const container = document.getElementById("sprite-list");
  container.innerHTML = "";
  Object.keys(project.sprites).forEach(sId => {
    const sp = project.sprites[sId];
    const row = document.createElement("div");
    row.className = `item-row ${sId === selectedSpriteId ? "active" : ""}`;
    row.textContent = `${sp.name} (${sp.frames.length} frames)`;
    row.addEventListener("click", () => {
      selectedSpriteId = sId;
      currentSpriteFrameIdx = 0;
      updateSpriteList();
      syncSpriteForm();
      renderSpriteCanvas();
    });
    container.appendChild(row);
  });
  syncSpriteForm();
}

function syncSpriteForm() {
  const sp = project.sprites[selectedSpriteId];
  if (!sp) return;
  document.getElementById("sprite-ink").value = sp.ink;
  document.getElementById("sprite-paper").value = sp.paper;
  document.getElementById("sprite-bright").checked = sp.bright;
  updateFrameCounter();
}

function updateFrameCounter() {
  const sp = project.sprites[selectedSpriteId];
  const total = sp ? sp.frames.length : 1;
  document.getElementById("frame-counter").textContent = `Frame ${currentSpriteFrameIdx + 1} / ${total}`;
}

function handleSpritePixelClick(e) {
  const canvas = document.getElementById("sprite-canvas");
  const rect = canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * (canvas.width / rect.width);
  const y = (e.clientY - rect.top) * (canvas.height / rect.height);
  const col = Math.floor(x / 24); // 384 / 16 = 24
  const row = Math.floor(y / 24);
  if (col < 0 || col >= 16 || row < 0 || row >= 16) return;

  const sp = project.sprites[selectedSpriteId];
  if (!sp || !sp.frames[currentSpriteFrameIdx]) return;
  const frame = sp.frames[currentSpriteFrameIdx];

  if (spriteTool === "pencil") {
    frame[row][col] = 1;
  } else if (spriteTool === "eraser") {
    frame[row][col] = 0;
  } else if (spriteTool === "fill") {
    floodFill(frame, row, col, frame[row][col], 1);
  }
  renderSpriteCanvas();
  renderRoomCanvas();
}

function invertSprite() {
  const sp = project.sprites[selectedSpriteId];
  if (!sp || !sp.frames[currentSpriteFrameIdx]) return;
  const frame = sp.frames[currentSpriteFrameIdx];
  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      frame[r][c] = frame[r][c] ? 0 : 1;
    }
  }
  renderSpriteCanvas();
}

function clearSprite() {
  const sp = project.sprites[selectedSpriteId];
  if (!sp || !sp.frames[currentSpriteFrameIdx]) return;
  const frame = sp.frames[currentSpriteFrameIdx];
  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      frame[r][c] = 0;
    }
  }
  renderSpriteCanvas();
}

function renderSpriteCanvas() {
  const canvas = document.getElementById("sprite-canvas");
  if (!canvas || !project) return;
  const ctx = canvas.getContext("2d");
  const sp = project.sprites[selectedSpriteId];
  if (!sp || !sp.frames[currentSpriteFrameIdx]) return;
  const frame = sp.frames[currentSpriteFrameIdx];

  const brightOffset = sp.bright ? 8 : 0;
  const inkColor = ZX_PALETTE[sp.ink + brightOffset] || "#ffff00";
  const paperColor = ZX_PALETTE[sp.paper] || "#000000";

  ctx.fillStyle = paperColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const cellSize = 24; // 384 / 16
  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      if (frame[r][c]) {
        ctx.fillStyle = inkColor;
        ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
      }
      // Grid line
      ctx.strokeStyle = "#1a1d26";
      ctx.strokeRect(c * cellSize, r * cellSize, cellSize, cellSize);
    }
  }
}

let previewFrame = 0;
function renderSpritePreview() {
  const canvas = document.getElementById("sprite-preview");
  if (!canvas || !project) return;
  const ctx = canvas.getContext("2d");
  const sp = project.sprites[selectedSpriteId];
  if (!sp || !sp.frames || sp.frames.length === 0) return;

  previewFrame = (previewFrame + 1) % sp.frames.length;
  const frame = sp.frames[previewFrame];

  const brightOffset = sp.bright ? 8 : 0;
  const inkColor = ZX_PALETTE[sp.ink + brightOffset] || "#ffff00";
  const paperColor = ZX_PALETTE[sp.paper] || "#000000";

  ctx.fillStyle = paperColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = inkColor;
  const pixelSize = 4; // 64 / 16
  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      if (frame[r] && frame[r][c]) {
        ctx.fillRect(c * pixelSize, r * pixelSize, pixelSize, pixelSize);
      }
    }
  }
}

// =============================================================================
// TAB 3: TILE EDITOR
// =============================================================================
function setupTileEditorEvents() {
  const canvas = document.getElementById("tile-canvas");

  canvas.addEventListener("mousedown", (e) => {
    isDrawingTile = true;
    handleTilePixelClick(e);
  });
  canvas.addEventListener("mousemove", (e) => {
    if (isDrawingTile && (tileTool === "pencil" || tileTool === "eraser")) {
      handleTilePixelClick(e);
    }
  });
  window.addEventListener("mouseup", () => {
    isDrawingTile = false;
  });

  // Tools
  const tTools = ["tile-tool-pencil", "tile-tool-eraser", "tile-tool-fill", "tile-tool-invert", "tile-tool-clear"];
  tTools.forEach(id => {
    document.getElementById(id).addEventListener("click", () => {
      tTools.forEach(b => document.getElementById(b).classList.remove("active"));
      document.getElementById(id).classList.add("active");
      tileTool = id.replace("tile-tool-", "");
      if (tileTool === "invert") invertTile();
      if (tileTool === "clear") clearTile();
    });
  });

  // Properties
  document.getElementById("tile-name-input").addEventListener("input", (e) => {
    if (project.tiles[selectedTileId]) {
      project.tiles[selectedTileId].name = e.target.value;
      updateTileEditorList();
      updateTilePalette();
    }
  });
  document.getElementById("tile-collision").addEventListener("change", (e) => {
    if (project.tiles[selectedTileId]) {
      project.tiles[selectedTileId].collision = e.target.value;
      updateTilePalette();
    }
  });
  document.getElementById("tile-score-val").addEventListener("input", (e) => {
    if (project.tiles[selectedTileId]) {
      project.tiles[selectedTileId].score_value = parseInt(e.target.value) || 0;
    }
  });
  document.getElementById("tile-ink").addEventListener("change", (e) => {
    if (project.tiles[selectedTileId]) {
      project.tiles[selectedTileId].ink = parseInt(e.target.value);
      renderTileCanvas();
      updateTilePalette();
      renderRoomCanvas();
    }
  });
  document.getElementById("tile-paper").addEventListener("change", (e) => {
    if (project.tiles[selectedTileId]) {
      project.tiles[selectedTileId].paper = parseInt(e.target.value);
      renderTileCanvas();
      updateTilePalette();
      renderRoomCanvas();
    }
  });
  document.getElementById("tile-bright").addEventListener("change", (e) => {
    if (project.tiles[selectedTileId]) {
      project.tiles[selectedTileId].bright = e.target.checked;
      renderTileCanvas();
      updateTilePalette();
      renderRoomCanvas();
    }
  });

  // Add Tile
  document.getElementById("btn-add-tile").addEventListener("click", () => {
    const existingIds = Object.keys(project.tiles).map(Number);
    const newId = existingIds.length ? Math.max(...existingIds) + 1 : 1;
    project.tiles[newId] = {
      id: newId,
      name: `Custom Tile ${newId}`,
      width: 16,
      height: 16,
      pixels: Array.from({length: 16}, () => Array(16).fill(0)),
      ink: 7,
      paper: 0,
      bright: true,
      collision: "solid",
      score_value: 0
    };
    selectedTileId = newId;
    updateTileEditorList();
    updateTilePalette();
    renderTileCanvas();
  });
}

function updateTileEditorList() {
  const container = document.getElementById("tile-editor-list");
  container.innerHTML = "";
  Object.keys(project.tiles).forEach(tIdStr => {
    const tId = parseInt(tIdStr);
    const tile = project.tiles[tId];
    const row = document.createElement("div");
    row.className = `item-row ${tId === selectedTileId ? "active" : ""}`;
    row.textContent = `${tId}: ${tile.name} [${tile.collision}]`;
    row.addEventListener("click", () => {
      selectedTileId = tId;
      updateTileEditorList();
      syncTileForm();
      renderTileCanvas();
    });
    container.appendChild(row);
  });
  syncTileForm();
}

function syncTileForm() {
  const tile = project.tiles[selectedTileId];
  if (!tile) return;
  document.getElementById("tile-name-input").value = tile.name;
  document.getElementById("tile-collision").value = tile.collision;
  document.getElementById("tile-score-val").value = tile.score_value || 0;
  document.getElementById("tile-ink").value = tile.ink;
  document.getElementById("tile-paper").value = tile.paper;
  document.getElementById("tile-bright").checked = tile.bright;
}

function handleTilePixelClick(e) {
  const canvas = document.getElementById("tile-canvas");
  const rect = canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * (canvas.width / rect.width);
  const y = (e.clientY - rect.top) * (canvas.height / rect.height);
  const col = Math.floor(x / 24);
  const row = Math.floor(y / 24);
  if (col < 0 || col >= 16 || row < 0 || row >= 16) return;

  const tile = project.tiles[selectedTileId];
  if (!tile || !tile.pixels) return;

  if (tileTool === "pencil") {
    tile.pixels[row][col] = 1;
  } else if (tileTool === "eraser") {
    tile.pixels[row][col] = 0;
  } else if (tileTool === "fill") {
    floodFill(tile.pixels, row, col, tile.pixels[row][col], 1);
  }
  renderTileCanvas();
  updateTilePalette();
  renderRoomCanvas();
}

function invertTile() {
  const tile = project.tiles[selectedTileId];
  if (!tile || !tile.pixels) return;
  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      tile.pixels[r][c] = tile.pixels[r][c] ? 0 : 1;
    }
  }
  renderTileCanvas();
  updateTilePalette();
  renderRoomCanvas();
}

function clearTile() {
  const tile = project.tiles[selectedTileId];
  if (!tile || !tile.pixels) return;
  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      tile.pixels[r][c] = 0;
    }
  }
  renderTileCanvas();
  updateTilePalette();
  renderRoomCanvas();
}

function renderTileCanvas() {
  const canvas = document.getElementById("tile-canvas");
  if (!canvas || !project) return;
  const ctx = canvas.getContext("2d");
  const tile = project.tiles[selectedTileId];
  if (!tile || !tile.pixels) return;

  const brightOffset = tile.bright ? 8 : 0;
  const inkColor = ZX_PALETTE[tile.ink + brightOffset] || "#ffffff";
  const paperColor = ZX_PALETTE[tile.paper] || "#000000";

  ctx.fillStyle = paperColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const cellSize = 24;
  for (let r = 0; r < 16; r++) {
    for (let c = 0; c < 16; c++) {
      if (tile.pixels[r] && tile.pixels[r][c]) {
        ctx.fillStyle = inkColor;
        ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
      }
      ctx.strokeStyle = "#1a1d26";
      ctx.strokeRect(c * cellSize, r * cellSize, cellSize, cellSize);
    }
  }
}

// Utility: Flood Fill
function floodFill(grid, r, c, targetVal, fillVal) {
  if (targetVal === fillVal) return;
  if (r < 0 || r >= 16 || c < 0 || c >= 16) return;
  if (grid[r][c] !== targetVal) return;
  grid[r][c] = fillVal;
  floodFill(grid, r + 1, c, targetVal, fillVal);
  floodFill(grid, r - 1, c, targetVal, fillVal);
  floodFill(grid, r, c + 1, targetVal, fillVal);
  floodFill(grid, r, c - 1, targetVal, fillVal);
}

// =============================================================================
// TAB 4: ZX SPECTRUM SIMULATOR (Real-time in-browser game engine)
// =============================================================================
let simRunning = false;
let simLoopId = null;
let simState = null;
const keyState = {};

function setupSimulatorEvents() {
  document.getElementById("sim-btn-start").addEventListener("click", () => {
    startSimulatorGame();
  });
  document.getElementById("sim-btn-pause").addEventListener("click", () => {
    simRunning = !simRunning;
    document.getElementById("sim-btn-pause").textContent = simRunning ? "⏸ Pause" : "▶ Resume";
    if (simRunning) simLoop();
  });
  document.getElementById("sim-btn-reset").addEventListener("click", () => {
    startSimulatorGame();
  });

  // Global Keyboard Listeners for Simulator
  window.addEventListener("keydown", (e) => {
    keyState[e.code] = true;
    keyState[e.key.toUpperCase()] = true;
    if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.code)) {
      // Prevent browser scroll
      if (document.getElementById("tab-simulator").classList.contains("active")) {
        e.preventDefault();
      }
    }
  });
  window.addEventListener("keyup", (e) => {
    keyState[e.code] = false;
    keyState[e.key.toUpperCase()] = false;
  });
}

function initSimulator() {
  if (!simState) {
    resetSimulatorState();
  }
  renderSimulatorFrame();
}

function resetSimulatorState() {
  if (!project) return;
  const cfg = project.config;
  const room = project.rooms[0] || { player_start: [2, 7], enemies: [] };
  const pStart = room.player_start || [2, 7];

  simState = {
    lives: cfg.start_lives,
    score: 0,
    keys: 0,
    currentRoom: 0,
    px: pStart[0] * 16,
    py: pStart[1] * 16,
    vx: 0,
    vy: 0,
    onGround: false,
    gameOver: false,
    gameWon: false,
    laserActive: false,
    lx: 0,
    ly: 0,
    // Deep clone room grids to allow item collection and block pushing
    roomGrids: project.rooms.map(r => r.tile_grid.map(row => [...row])),
    enemies: (room.enemies || []).map(e => ({
      x: e.x * 16,
      y: e.y * 16,
      minX: (e.patrol_min || 0) * 16,
      maxX: (e.patrol_max || 15) * 16,
      dir: 1,
      alive: true
    }))
  };
}

function startSimulatorGame() {
  resetSimulatorState();
  simRunning = true;
  document.getElementById("sim-btn-pause").textContent = "⏸ Pause";
  playSweep(400, 800, 0.15); // Start chirp
  if (simLoopId) cancelAnimationFrame(simLoopId);
  simLoop();
}

let lastFrameTime = performance.now();
let fpsCounter = 50;

function simLoop() {
  if (!simRunning) return;

  const now = performance.now();
  const dt = now - lastFrameTime;
  lastFrameTime = now;
  fpsCounter = Math.round(1000 / Math.max(dt, 1));

  updateSimulatorLogic();
  renderSimulatorFrame();
  updateTelemetry();

  simLoopId = requestAnimationFrame(simLoop);
}

function updateSimulatorLogic() {
  if (!simState || simState.gameOver || simState.gameWon) return;

  const cfg = project.config;
  const gType = cfg.game_type.toLowerCase();

  // Read Input
  const left = keyState["KeyO"] || keyState["ArrowLeft"] || keyState["KeyA"];
  const right = keyState["KeyP"] || keyState["ArrowRight"] || keyState["KeyD"];
  const up = keyState["KeyQ"] || keyState["ArrowUp"] || keyState["KeyW"];
  const down = keyState["KeyA"] || keyState["ArrowDown"] || keyState["KeyS"];
  const fire = keyState["Space"] || keyState["Enter"];

  // ---------------------------------------------------------------------------
  // 1. PLATFORMER LOGIC
  // ---------------------------------------------------------------------------
  if (gType === "platformer") {
    // Left/Right
    if (left) simState.px = Math.max(8, simState.px - cfg.player_speed);
    if (right) simState.px = Math.min(232, simState.px + cfg.player_speed);

    // Jump
    if (fire && simState.onGround) {
      simState.vy = -cfg.jump_strength;
      simState.onGround = false;
      playSweep(250, 750, 0.12);
    }

    // Gravity
    simState.vy = Math.min(8, simState.vy + (cfg.gravity || 1));
    simState.py += simState.vy;

    // Floor & Collision Check (Check feet at center-bottom)
    const feetCol = Math.floor((simState.px + 8) / 16);
    const feetRow = Math.floor((simState.py + 16) / 16);
    const grid = simState.roomGrids[simState.currentRoom];
    const tileId = (grid && grid[feetRow]) ? grid[feetRow][feetCol] : 0;
    const tile = project.tiles[tileId];

    if (tile) {
      if (tile.collision === "solid" || (tile.collision === "platform" && simState.vy >= 0)) {
        simState.py = feetRow * 16 - 16;
        simState.vy = 0;
        simState.onGround = true;
      } else if (tile.collision === "hazard") {
        hitHazard();
      } else if (tile.collision === "collectible") {
        grid[feetRow][feetCol] = 0; // Collect
        simState.score += (tile.score_value || 100);
        playBeep(880, 0.08);
      } else if (tile.collision === "exit") {
        levelExit();
      } else {
        simState.onGround = false;
      }
    }
  }

  // ---------------------------------------------------------------------------
  // 2. TOP-DOWN ADVENTURE LOGIC
  // ---------------------------------------------------------------------------
  else if (gType === "topdown") {
    let nx = simState.px;
    let ny = simState.py;
    if (left) nx -= cfg.player_speed;
    if (right) nx += cfg.player_speed;
    if (up) ny -= cfg.player_speed;
    if (down) ny += cfg.player_speed;

    // Room boundaries & exits
    const room = project.rooms[simState.currentRoom];
    if (nx < 0) {
      if (room.exits.west !== null) switchRoom(room.exits.west, 230, simState.py);
      return;
    }
    if (nx > 240) {
      if (room.exits.east !== null) switchRoom(room.exits.east, 8, simState.py);
      return;
    }
    if (ny < 0) {
      if (room.exits.north !== null) switchRoom(room.exits.north, simState.px, 150);
      return;
    }
    if (ny > 160) {
      if (room.exits.south !== null) switchRoom(room.exits.south, simState.px, 8);
      return;
    }

    // Tile collision
    const col = Math.floor((nx + 8) / 16);
    const row = Math.floor((ny + 8) / 16);
    const grid = simState.roomGrids[simState.currentRoom];
    const tileId = (grid && grid[row]) ? grid[row][col] : 0;
    const tile = project.tiles[tileId];

    if (!tile || tile.collision !== "solid") {
      simState.px = nx;
      simState.py = ny;
    }
    if (tile) {
      if (tile.collision === "collectible") {
        grid[row][col] = 0;
        simState.score += (tile.score_value || 100);
        playBeep(950, 0.08);
      } else if (tile.collision === "key") {
        grid[row][col] = 0;
        simState.keys++;
        playSweep(500, 1000, 0.15);
      } else if (tile.collision === "door" && simState.keys > 0) {
        grid[row][col] = 0; // Open door
        simState.keys--;
        playSweep(400, 200, 0.1);
      } else if (tile.collision === "exit") {
        levelExit();
      }
    }
  }

  // ---------------------------------------------------------------------------
  // 3. SHOOT 'EM UP LOGIC
  // ---------------------------------------------------------------------------
  else if (gType === "shmup") {
    if (left) simState.px = Math.max(8, simState.px - cfg.player_speed);
    if (right) simState.px = Math.min(232, simState.px + cfg.player_speed);

    // Fire laser
    if (fire && !simState.laserActive) {
      simState.laserActive = true;
      simState.lx = simState.px + 4;
      simState.ly = simState.py - 8;
      playSweep(900, 300, 0.08);
    }

    if (simState.laserActive) {
      simState.ly -= 8;
      if (simState.ly < 0) simState.laserActive = false;

      // Laser hitting enemy
      simState.enemies.forEach(e => {
        if (e.alive && Math.abs(simState.lx - e.x) < 14 && Math.abs(simState.ly - e.y) < 14) {
          e.alive = false;
          simState.laserActive = false;
          simState.score += 250;
          playNoise(0.15);
          if (simState.score >= cfg.win_score) {
            simState.gameWon = true;
            playSweep(400, 1200, 0.3);
          }
        }
      });
    }
  }

  // ---------------------------------------------------------------------------
  // 4. PUZZLE / SOKOBAN LOGIC
  // ---------------------------------------------------------------------------
  else if (gType === "puzzle") {
    // Grid stepping
    if (simState.stepCooldown && simState.stepCooldown > 0) {
      simState.stepCooldown--;
    } else {
      let dx = 0, dy = 0;
      if (left) dx = -1;
      else if (right) dx = 1;
      else if (up) dy = -1;
      else if (down) dy = 1;

      if (dx !== 0 || dy !== 0) {
        simState.stepCooldown = 8;
        const curCol = Math.floor(simState.px / 16);
        const curRow = Math.floor(simState.py / 16);
        const targetCol = curCol + dx;
        const targetRow = curRow + dy;
        const grid = simState.roomGrids[simState.currentRoom];

        if (targetCol >= 0 && targetCol < 16 && targetRow >= 0 && targetRow < 11) {
          const tId = grid[targetRow][targetCol];
          const tile = project.tiles[tId];

          if (!tile || tile.collision === "empty") {
            simState.px = targetCol * 16;
            simState.py = targetRow * 16;
          } else if (tile.collision === "pushable") {
            // Check beyond space
            const bCol = targetCol + dx;
            const bRow = targetRow + dy;
            if (bCol >= 0 && bCol < 16 && bRow >= 0 && bRow < 11) {
              const bTile = project.tiles[grid[bRow][bCol]];
              if (!bTile || bTile.collision === "empty") {
                grid[bRow][bCol] = tId; // Move boulder
                grid[targetRow][targetCol] = 0;
                simState.px = targetCol * 16;
                simState.py = targetRow * 16;
                playSweep(200, 300, 0.08);
              }
            }
          } else if (tile.collision === "collectible") {
            grid[targetRow][targetCol] = 0;
            simState.score += (tile.score_value || 100);
            simState.px = targetCol * 16;
            simState.py = targetRow * 16;
            playBeep(900, 0.08);
          } else if (tile.collision === "exit") {
            levelExit();
          }
        }
      }
    }
  }

  // ---------------------------------------------------------------------------
  // 5. ADVENTURE LOGIC
  // ---------------------------------------------------------------------------
  else if (gType === "adventure") {
    if (simState.stepCooldown && simState.stepCooldown > 0) {
      simState.stepCooldown--;
    } else {
      const room = project.rooms[simState.currentRoom];
      if (up && room.exits.north !== null) {
        simState.stepCooldown = 15;
        switchRoom(room.exits.north, simState.px, simState.py);
      } else if (down && room.exits.south !== null) {
        simState.stepCooldown = 15;
        switchRoom(room.exits.south, simState.px, simState.py);
      } else if (left && room.exits.west !== null) {
        simState.stepCooldown = 15;
        switchRoom(room.exits.west, simState.px, simState.py);
      } else if (right && room.exits.east !== null) {
        simState.stepCooldown = 15;
        switchRoom(room.exits.east, simState.px, simState.py);
      } else if (fire) {
        simState.stepCooldown = 15;
        // Inspect
        playBeep(600, 0.1);
        if (simState.currentRoom === 0 && simState.keys === 0) {
          simState.keys = 1;
          alert("YOU PICKED UP THE BRASS KEY!");
        } else if (simState.currentRoom === 1 && simState.keys > 0) {
          simState.gameWon = true;
          playSweep(300, 900, 0.4);
        }
      }
    }
  }

  // Enemy Patrol AI
  simState.enemies.forEach(e => {
    if (!e.alive) return;
    e.x += e.dir;
    if (e.x >= e.maxX) e.dir = -1;
    if (e.x <= e.minX) e.dir = 1;

    // Collision with player
    if (Math.abs(simState.px - e.x) < 12 && Math.abs(simState.py - e.y) < 12) {
      hitHazard();
    }
  });
}

function hitHazard() {
  playNoise(0.2);
  simState.lives--;
  if (simState.lives <= 0) {
    simState.gameOver = true;
    playSweep(400, 100, 0.4);
  } else {
    // Reset player position
    const room = project.rooms[simState.currentRoom];
    const pStart = (room && room.player_start) ? room.player_start : [2, 7];
    simState.px = pStart[0] * 16;
    simState.py = pStart[1] * 16;
    simState.vy = 0;
  }
}

function switchRoom(nextRoomId, px, py) {
  if (nextRoomId === null || nextRoomId === undefined || !project.rooms[nextRoomId]) return;
  simState.currentRoom = nextRoomId;
  simState.px = px;
  simState.py = py;
  simState.vy = 0;
  // Load enemies for new room
  const room = project.rooms[nextRoomId];
  simState.enemies = (room.enemies || []).map(e => ({
    x: e.x * 16,
    y: e.y * 16,
    minX: (e.patrol_min || 0) * 16,
    maxX: (e.patrol_max || 15) * 16,
    dir: 1,
    alive: true
  }));
  playSweep(300, 600, 0.1);
}

function levelExit() {
  playSweep(500, 1000, 0.25);
  const next = simState.currentRoom + 1;
  if (next < project.rooms.length) {
    switchRoom(next, 32, 64);
  } else {
    simState.gameWon = true;
    playSweep(400, 1200, 0.4);
  }
}

function renderSimulatorFrame() {
  const canvas = document.getElementById("sim-canvas");
  if (!canvas || !project) return;
  const ctx = canvas.getContext("2d");

  // Border Color
  const borderColor = ZX_PALETTE[project.config.border_color] || "#000000";
  ctx.fillStyle = borderColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Inner Screen: 256x192 at 2x scale = 512x384
  const paperColor = ZX_PALETTE[project.config.paper_color] || "#000000";
  ctx.fillStyle = paperColor;
  ctx.fillRect(0, 0, 512, 352); // 176px game area * 2

  if (!simState) return;

  // 1. Draw Tiles of current room
  const grid = simState.roomGrids[simState.currentRoom];
  if (grid) {
    for (let r = 0; r < 11; r++) {
      for (let c = 0; c < 16; c++) {
        const tileId = grid[r][c];
        drawTileToCanvas(ctx, tileId, c * 32, r * 32, 32, 32);
      }
    }
  }

  // 2. Draw Laser (Shmup)
  if (simState.laserActive) {
    ctx.fillStyle = "#ffff00";
    ctx.fillRect(simState.lx * 2, simState.ly * 2, 8, 16);
  }

  // 3. Draw Enemies
  simState.enemies.forEach(e => {
    if (e.alive) {
      drawSpriteToCanvas(ctx, "enemy_bat", e.x * 2, e.y * 2, 32, 32);
    }
  });

  // 4. Draw Player
  if (!simState.gameOver) {
    drawSpriteToCanvas(ctx, "player", simState.px * 2, simState.py * 2, 32, 32);
  }

  // 5. Draw HUD Bar (Rows 22-23 = bottom 32 pixels)
  ctx.fillStyle = "#0000d7";
  ctx.fillRect(0, 352, 512, 32);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 14px 'Courier New', monospace";
  ctx.fillText(`SCORE: ${simState.score}`, 16, 373);
  ctx.fillText(`LIVES: ${simState.lives}`, 200, 373);
  ctx.fillText(`KEYS: ${simState.keys}`, 340, 373);

  // Game Over / Win Overlays
  if (simState.gameOver) {
    ctx.fillStyle = "rgba(0, 0, 0, 0.75)";
    ctx.fillRect(80, 120, 352, 110);
    ctx.strokeStyle = "#ff0000";
    ctx.lineWidth = 3;
    ctx.strokeRect(80, 120, 352, 110);
    ctx.fillStyle = "#ff0000";
    ctx.font = "bold 24px 'Courier New', monospace";
    ctx.fillText("GAME OVER", 180, 165);
    ctx.fillStyle = "#ffffff";
    ctx.font = "14px 'Courier New', monospace";
    ctx.fillText("PRESS RESTART TO PLAY AGAIN", 130, 200);
  }

  if (simState.gameWon) {
    ctx.fillStyle = "rgba(0, 0, 0, 0.85)";
    ctx.fillRect(80, 120, 352, 110);
    ctx.strokeStyle = "#ffff00";
    ctx.lineWidth = 3;
    ctx.strokeRect(80, 120, 352, 110);
    ctx.fillStyle = "#ffff00";
    ctx.font = "bold 24px 'Courier New', monospace";
    ctx.fillText("VICTORY!", 195, 165);
    ctx.fillStyle = "#00ffff";
    ctx.font = "14px 'Courier New', monospace";
    ctx.fillText("CONGRATULATIONS, CHAMPION!", 135, 200);
  }
}

function updateTelemetry() {
  if (!simState || !project) return;
  document.getElementById("tel-title").textContent = project.config.title;
  document.getElementById("tel-genre").textContent = project.config.game_type.toUpperCase();
  document.getElementById("tel-player-pos").textContent = `${Math.round(simState.px)}, ${Math.round(simState.py)}`;
  document.getElementById("tel-score").textContent = simState.score;
  document.getElementById("tel-lives").textContent = simState.lives;
  document.getElementById("tel-room").textContent = `${simState.currentRoom} (${project.rooms[simState.currentRoom]?.name || ""})`;
  document.getElementById("tel-fps").textContent = `${fpsCounter} FPS`;
}

// =============================================================================
// TAB 6: GAME CONFIGURATION
// =============================================================================
function setupSettingsEvents() {
  const cfg = project?.config;

  document.getElementById("cfg-title").addEventListener("input", (e) => {
    project.config.title = e.target.value.toUpperCase();
  });
  document.getElementById("cfg-author").addEventListener("input", (e) => {
    project.config.author = e.target.value.toUpperCase();
  });
  document.getElementById("cfg-year").addEventListener("input", (e) => {
    project.config.year = parseInt(e.target.value) || 1983;
  });
  document.getElementById("cfg-genre").addEventListener("change", (e) => {
    project.config.game_type = e.target.value;
  });
  document.getElementById("cfg-border").addEventListener("change", (e) => {
    project.config.border_color = parseInt(e.target.value);
    renderSimulatorFrame();
  });
  document.getElementById("cfg-paper").addEventListener("change", (e) => {
    project.config.paper_color = parseInt(e.target.value);
    renderRoomCanvas();
    renderSimulatorFrame();
  });
  document.getElementById("cfg-ink").addEventListener("change", (e) => {
    project.config.ink_color = parseInt(e.target.value);
  });
  document.getElementById("cfg-bright").addEventListener("change", (e) => {
    project.config.bright = e.target.checked;
  });
  document.getElementById("cfg-lives").addEventListener("input", (e) => {
    project.config.start_lives = parseInt(e.target.value) || 3;
  });
  document.getElementById("cfg-speed").addEventListener("input", (e) => {
    project.config.player_speed = parseInt(e.target.value) || 2;
  });
  document.getElementById("cfg-gravity").addEventListener("input", (e) => {
    project.config.gravity = parseInt(e.target.value) || 2;
  });
  document.getElementById("cfg-jump").addEventListener("input", (e) => {
    project.config.jump_strength = parseInt(e.target.value) || 7;
  });
  document.getElementById("cfg-win-score").addEventListener("input", (e) => {
    project.config.win_score = parseInt(e.target.value) || 1000;
  });
  document.getElementById("cfg-controls").addEventListener("change", (e) => {
    project.config.controls = e.target.value;
  });
}

function updateSettingsForm() {
  const cfg = project.config;
  document.getElementById("cfg-title").value = cfg.title;
  document.getElementById("cfg-author").value = cfg.author;
  document.getElementById("cfg-year").value = cfg.year;
  document.getElementById("cfg-genre").value = cfg.game_type;
  document.getElementById("cfg-border").value = cfg.border_color;
  document.getElementById("cfg-paper").value = cfg.paper_color;
  document.getElementById("cfg-ink").value = cfg.ink_color;
  document.getElementById("cfg-bright").checked = cfg.bright;
  document.getElementById("cfg-lives").value = cfg.start_lives;
  document.getElementById("cfg-speed").value = cfg.player_speed;
  document.getElementById("cfg-gravity").value = cfg.gravity;
  document.getElementById("cfg-jump").value = cfg.jump_strength;
  document.getElementById("cfg-win-score").value = cfg.win_score;
  document.getElementById("cfg-controls").value = cfg.controls;
}
