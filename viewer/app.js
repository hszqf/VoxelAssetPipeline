const DATASETS = [
  {
    id: "design-sheet",
    name: "Design sheet trial",
    manifest: "/examples/design_sheet_trial/manifest.json",
    cellResolution: 64,
  },
  {
    id: "quick-trial",
    name: "Quick trial",
    manifest: "/examples/quick_trial/manifest.json",
    cellResolution: 64,
  },
  {
    id: "dog-trial",
    name: "Dog trial",
    manifest: "/examples/dog_trial/manifest.json",
    cellResolution: 64,
  },
];

const DEFAULT_CELL_RESOLUTION = 8;

const state = {
  datasets: new Map(),
  currentDataset: DATASETS[0].id,
  currentAsset: null,
  currentModel: null,
  yaw: -Math.PI / 4,
  pitch: -0.55,
  zoom: 28,
  dragging: false,
  lastX: 0,
  lastY: 0,
  infoCollapsed: true,
  layoutLeft: 320,
  layoutRight: 420,
  layoutBottom: 280,
  layoutDragging: null,
};

const canvas = document.getElementById("viewer");
const ctx = canvas.getContext("2d", { alpha: true });
const datasetSelect = document.getElementById("datasetSelect");
const assetList = document.getElementById("assetList");
const resetViewButton = document.getElementById("resetView");
const assetName = document.getElementById("assetName");
const assetSize = document.getElementById("assetSize");
const assetVoxels = document.getElementById("assetVoxels");
const assetScale = document.getElementById("assetScale");
const assetCells = document.getElementById("assetCells");
const assetObserved = document.getElementById("assetObserved");
const floatingInfo = document.getElementById("floatingInfo");
const infoToggle = document.getElementById("infoToggle");
const referenceName = document.getElementById("referenceName");
const referenceViews = document.getElementById("referenceViews");
const leftResize = document.getElementById("leftResize");
const rightResize = document.getElementById("rightResize");

function cssSize() {
  const rect = canvas.getBoundingClientRect();
  return { width: rect.width, height: rect.height };
}

function resizeCanvas() {
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const { width, height } = cssSize();
  const nextW = Math.max(1, Math.round(width * dpr));
  const nextH = Math.max(1, Math.round(height * dpr));
  if (canvas.width !== nextW || canvas.height !== nextH) {
    canvas.width = nextW;
    canvas.height = nextH;
  }
  render();
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function isCompactLayout() {
  return window.matchMedia("(max-width: 1120px)").matches;
}

function applyLayoutVars() {
  document.documentElement.style.setProperty("--left-pane", `${state.layoutLeft}px`);
  document.documentElement.style.setProperty("--right-pane", `${state.layoutRight}px`);
  document.documentElement.style.setProperty("--bottom-pane", `${state.layoutBottom}px`);
  resizeCanvas();
}

function startLayoutResize(kind, event) {
  state.layoutDragging = kind;
  event.preventDefault();
  event.currentTarget.classList.add("active");
  document.body.classList.add("resizing");
  document.body.classList.toggle("resizing-reference", kind === "reference");
  event.currentTarget.setPointerCapture(event.pointerId);
}

function updateLayoutResize(event) {
  if (!state.layoutDragging) {
    return;
  }

  if (state.layoutDragging === "left") {
    const maxLeft = isCompactLayout()
      ? Math.min(460, window.innerWidth - 360)
      : Math.min(520, window.innerWidth - state.layoutRight - 380);
    state.layoutLeft = clamp(event.clientX, 220, Math.max(220, maxLeft));
  } else if (isCompactLayout()) {
    const maxBottom = Math.min(520, window.innerHeight - 260);
    state.layoutBottom = clamp(window.innerHeight - event.clientY, 180, Math.max(180, maxBottom));
  } else {
    const maxRight = Math.min(680, window.innerWidth - state.layoutLeft - 380);
    state.layoutRight = clamp(window.innerWidth - event.clientX, 260, Math.max(260, maxRight));
  }

  applyLayoutVars();
}

function finishLayoutResize(event) {
  if (!state.layoutDragging) {
    return;
  }

  state.layoutDragging = null;
  document.body.classList.remove("resizing", "resizing-reference");
  leftResize.classList.remove("active");
  rightResize.classList.remove("active");
  if (event.currentTarget && event.currentTarget.releasePointerCapture) {
    try {
      event.currentTarget.releasePointerCapture(event.pointerId);
    } catch {
      // Pointer capture can already be released when the pointer leaves the tab.
    }
  }
}

function readChunkId(view, offset) {
  return String.fromCharCode(
    view.getUint8(offset),
    view.getUint8(offset + 1),
    view.getUint8(offset + 2),
    view.getUint8(offset + 3),
  );
}

function defaultPalette() {
  return Array.from({ length: 256 }, (_, i) => [i, i, i, 255]);
}

function parseVox(buffer) {
  const view = new DataView(buffer);
  if (readChunkId(view, 0) !== "VOX ") {
    throw new Error("Invalid VOX header");
  }

  const version = view.getUint32(4, true);
  let size = { width: 0, height: 0, depth: 0 };
  let voxels = [];
  let palette = defaultPalette();

  function walk(offset, end) {
    while (offset < end) {
      const id = readChunkId(view, offset);
      const contentSize = view.getUint32(offset + 4, true);
      const childrenSize = view.getUint32(offset + 8, true);
      const contentStart = offset + 12;
      const contentEnd = contentStart + contentSize;
      const childrenEnd = contentEnd + childrenSize;

      if (id === "SIZE") {
        const sx = view.getUint32(contentStart, true);
        const sy = view.getUint32(contentStart + 4, true);
        const sz = view.getUint32(contentStart + 8, true);
        size = { width: sx, depth: sy, height: sz };
      } else if (id === "XYZI") {
        const count = view.getUint32(contentStart, true);
        voxels = [];
        let p = contentStart + 4;
        for (let i = 0; i < count; i += 1) {
          const x = view.getUint8(p);
          const z = view.getUint8(p + 1);
          const y = view.getUint8(p + 2);
          const colorIndex = view.getUint8(p + 3);
          voxels.push({ x, y, z, colorIndex });
          p += 4;
        }
      } else if (id === "RGBA") {
        palette = [];
        let p = contentStart;
        for (let i = 0; i < 256; i += 1) {
          palette.push([
            view.getUint8(p),
            view.getUint8(p + 1),
            view.getUint8(p + 2),
            view.getUint8(p + 3),
          ]);
          p += 4;
        }
      }

      if (childrenSize > 0) {
        walk(contentEnd, childrenEnd);
      }

      offset = childrenEnd;
    }
  }

  walk(8, view.byteLength);

  return {
    version,
    size,
    voxels,
    palette,
  };
}

function makeOccupancy(voxels) {
  const set = new Set();
  for (const v of voxels) {
    set.add(`${v.x},${v.y},${v.z}`);
  }
  return set;
}

function rotate(point) {
  const cy = Math.cos(state.yaw);
  const sy = Math.sin(state.yaw);
  const cp = Math.cos(state.pitch);
  const sp = Math.sin(state.pitch);

  const x1 = point.x * cy - point.z * sy;
  const z1 = point.x * sy + point.z * cy;
  const y1 = point.y;

  return {
    x: x1,
    y: y1 * cp - z1 * sp,
    z: y1 * sp + z1 * cp,
  };
}

function project(point, centerX, centerY) {
  const r = rotate(point);
  return {
    x: centerX + r.x * state.zoom,
    y: centerY - r.y * state.zoom,
    depth: r.z,
  };
}

const FACE_DEFS = [
  {
    neighbor: [1, 0, 0],
    normal: { x: 1, y: 0, z: 0 },
    corners: [[1, 0, 0], [1, 0, 1], [1, 1, 1], [1, 1, 0]],
  },
  {
    neighbor: [-1, 0, 0],
    normal: { x: -1, y: 0, z: 0 },
    corners: [[0, 0, 1], [0, 0, 0], [0, 1, 0], [0, 1, 1]],
  },
  {
    neighbor: [0, 1, 0],
    normal: { x: 0, y: 1, z: 0 },
    corners: [[0, 1, 0], [1, 1, 0], [1, 1, 1], [0, 1, 1]],
  },
  {
    neighbor: [0, -1, 0],
    normal: { x: 0, y: -1, z: 0 },
    corners: [[0, 0, 1], [1, 0, 1], [1, 0, 0], [0, 0, 0]],
  },
  {
    neighbor: [0, 0, 1],
    normal: { x: 0, y: 0, z: 1 },
    corners: [[1, 0, 1], [0, 0, 1], [0, 1, 1], [1, 1, 1]],
  },
  {
    neighbor: [0, 0, -1],
    normal: { x: 0, y: 0, z: -1 },
    corners: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
  },
];

const LIGHT = normalize({ x: -0.45, y: 0.8, z: 0.35 });

function normalize(v) {
  const len = Math.hypot(v.x, v.y, v.z) || 1;
  return { x: v.x / len, y: v.y / len, z: v.z / len };
}

function dot(a, b) {
  return a.x * b.x + a.y * b.y + a.z * b.z;
}

function wrapAngle(angle) {
  const twoPi = Math.PI * 2;
  return ((angle + Math.PI) % twoPi + twoPi) % twoPi - Math.PI;
}

function colorToCss(rgba, factor) {
  const [r, g, b, a] = rgba;
  const rr = Math.min(255, Math.max(0, Math.round(r * factor)));
  const gg = Math.min(255, Math.max(0, Math.round(g * factor)));
  const bb = Math.min(255, Math.max(0, Math.round(b * factor)));
  const aa = Math.min(1, Math.max(0, a / 255));
  return `rgba(${rr}, ${gg}, ${bb}, ${aa})`;
}

function modelFrame(model) {
  const { width, height, depth } = model.size;
  const gameCell = currentCellResolution();
  return {
    width: Math.max(gameCell, Math.ceil(width / gameCell) * gameCell),
    height: Math.max(gameCell, Math.ceil(height / gameCell) * gameCell),
    depth: Math.max(gameCell, Math.ceil(depth / gameCell) * gameCell),
  };
}

function buildFaces(model) {
  const occ = makeOccupancy(model.voxels);
  const frame = modelFrame(model);
  const offset = {
    x: (frame.width - model.size.width) / 2,
    y: 0,
    z: (frame.depth - model.size.depth) / 2,
  };
  const origin = {
    x: frame.width / 2,
    y: frame.height / 2,
    z: frame.depth / 2,
  };
  const faces = [];

  for (const voxel of model.voxels) {
    for (const def of FACE_DEFS) {
      const [nx, ny, nz] = def.neighbor;
      if (occ.has(`${voxel.x + nx},${voxel.y + ny},${voxel.z + nz}`)) {
        continue;
      }

      const rn = rotate(def.normal);
      if (rn.z <= -0.05) {
        continue;
      }

      const worldCorners = def.corners.map(([cx, cy, cz]) => ({
        x: voxel.x + cx + offset.x - origin.x,
        y: voxel.y + cy + offset.y - origin.y,
        z: voxel.z + cz + offset.z - origin.z,
      }));
      const avg = worldCorners.reduce((acc, p) => {
        const rp = rotate(p);
        return acc + rp.z;
      }, 0) / worldCorners.length;
      const lightAmount = Math.max(0, dot(def.normal, LIGHT));
      const factor = 0.66 + lightAmount * 0.46;
      faces.push({
        corners: worldCorners,
        depth: avg,
        color: colorToCss(model.palette[voxel.colorIndex - 1] || [255, 0, 255, 255], factor),
      });
    }
  }

  faces.sort((a, b) => a.depth - b.depth);
  return { faces, frame, origin };
}

function gridLines(frame) {
  const lines = [];
  const gameCell = currentCellResolution();
  for (let x = 0; x <= frame.width; x += gameCell) {
    for (let z = 0; z <= frame.depth; z += gameCell) {
      lines.push([[x, 0, z], [x, frame.height, z]]);
    }
  }
  for (let y = 0; y <= frame.height; y += gameCell) {
    for (let z = 0; z <= frame.depth; z += gameCell) {
      lines.push([[0, y, z], [frame.width, y, z]]);
    }
    for (let x = 0; x <= frame.width; x += gameCell) {
      lines.push([[x, y, 0], [x, y, frame.depth]]);
    }
  }
  for (let x = 0; x <= frame.width; x += gameCell) {
    for (let y = 0; y <= frame.height; y += gameCell) {
      lines.push([[x, y, 0], [x, y, frame.depth]]);
    }
  }
  return lines;
}

function boxEdgeLines(x0, y0, z0, x1, y1, z1) {
  return [
    [[x0, y0, z0], [x1, y0, z0]],
    [[x1, y0, z0], [x1, y0, z1]],
    [[x1, y0, z1], [x0, y0, z1]],
    [[x0, y0, z1], [x0, y0, z0]],
    [[x0, y1, z0], [x1, y1, z0]],
    [[x1, y1, z0], [x1, y1, z1]],
    [[x1, y1, z1], [x0, y1, z1]],
    [[x0, y1, z1], [x0, y1, z0]],
    [[x0, y0, z0], [x0, y1, z0]],
    [[x1, y0, z0], [x1, y1, z0]],
    [[x1, y0, z1], [x1, y1, z1]],
    [[x0, y0, z1], [x0, y1, z1]],
  ];
}

function drawLines(lines, origin, centerX, centerY) {
  for (const [[x0, y0, z0], [x1, y1, z1]] of lines) {
    const p0 = project({ x: x0 - origin.x, y: y0 - origin.y, z: z0 - origin.z }, centerX, centerY);
    const p1 = project({ x: x1 - origin.x, y: y1 - origin.y, z: z1 - origin.z }, centerX, centerY);
    ctx.beginPath();
    ctx.moveTo(p0.x, p0.y);
    ctx.lineTo(p1.x, p1.y);
    ctx.stroke();
  }
}

function drawWireframe(frame, centerX, centerY) {
  const origin = { x: frame.width / 2, y: frame.height / 2, z: frame.depth / 2 };

  ctx.save();
  ctx.lineWidth = Math.max(1, window.devicePixelRatio || 1);
  ctx.strokeStyle = "rgba(107, 121, 127, 0.28)";
  ctx.setLineDash([7, 5]);
  drawLines(gridLines(frame), origin, centerX, centerY);

  ctx.lineWidth = Math.max(2, (window.devicePixelRatio || 1) * 1.5);
  ctx.strokeStyle = "rgba(33, 182, 215, 0.95)";
  ctx.setLineDash([9, 5]);
  drawLines(boxEdgeLines(0, 0, 0, currentCellResolution(), currentCellResolution(), currentCellResolution()), origin, centerX, centerY);
  ctx.restore();
}

function render() {
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  if (!state.currentModel) {
    ctx.save();
    ctx.fillStyle = "#706c62";
    ctx.font = `${16 * dpr}px sans-serif`;
    ctx.textAlign = "center";
    ctx.fillText("Loading vox assets...", width / 2, height / 2);
    ctx.restore();
    return;
  }

  const centerX = width * 0.52;
  const centerY = height * 0.55;
  const { faces, frame } = buildFaces(state.currentModel);
  drawWireframe(frame, centerX, centerY);

  ctx.save();
  ctx.lineWidth = Math.max(0.6, dpr * 0.75);
  ctx.strokeStyle = "rgba(24, 24, 22, 0.16)";
  for (const face of faces) {
    const points = face.corners.map((p) => project(p, centerX, centerY));
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i += 1) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.closePath();
    ctx.fillStyle = face.color;
    ctx.fill();
    ctx.stroke();
  }
  ctx.restore();
}

function updateInfo() {
  const asset = state.currentAsset;
  const model = state.currentModel;
  if (!asset || !model) {
    return;
  }

  const frame = modelFrame(model);
  const gameCell = currentCellResolution();
  assetName.textContent = asset.name;
  assetSize.textContent = `${model.size.width} x ${model.size.height} x ${model.size.depth}`;
  assetVoxels.textContent = `${model.voxels.length}`;
  assetScale.textContent = asset.scale_tier || asset.scaleTier || "-";
  assetCells.textContent = `${frame.width / gameCell} x ${frame.height / gameCell} x ${frame.depth / gameCell} (${gameCell} vox/cell)`;
  assetObserved.textContent = asset.observed || "";
  updateReference(asset);
}

function currentCellResolution() {
  const dataset = state.datasets.get(state.currentDataset);
  return state.currentAsset?.cell_resolution || dataset?.cellResolution || DEFAULT_CELL_RESOLUTION;
}

function referenceViewsFor(asset) {
  const preferredOrder = ["iso", "side", "front", "top"];
  if (Array.isArray(asset.reference_views) && asset.reference_views.length > 0) {
    const byId = new Map(asset.reference_views.map((view) => [view.id, view]));
    const ordered = preferredOrder.map((id) => byId.get(id)).filter(Boolean);
    return ordered.length > 0 ? ordered : asset.reference_views.slice(0, 4);
  }
  if (asset.source_image) {
    return [{ id: "source", label: "Source", path: asset.source_image }];
  }
  return [];
}

function updateReference(asset) {
  const views = referenceViewsFor(asset);
  referenceViews.innerHTML = "";
  if (!views.length) {
    referenceName.textContent = "No source";
    return;
  }

  referenceName.textContent = asset.name;
  for (const view of views) {
    const path = normalizePath(view.path);
    const label = view.label || view.id || path.split("/").pop() || path;
    const local = embeddedImage(path);
    const card = document.createElement("figure");
    card.className = "reference-card";

    const caption = document.createElement("figcaption");
    caption.textContent = label;

    const image = document.createElement("img");
    image.alt = `${asset.name} ${label}`;
    image.src = local ? `data:image/png;base64,${local}` : `/${path}`;

    card.append(caption, image);
    referenceViews.appendChild(card);
  }
}

function setInfoCollapsed(collapsed) {
  state.infoCollapsed = collapsed;
  floatingInfo.classList.toggle("collapsed", collapsed);
  infoToggle.textContent = collapsed ? "+" : "-";
  infoToggle.title = collapsed ? "Expand info" : "Collapse info";
}

function normalizePath(path) {
  return path.replace(/\\/g, "/").replace(/^\/+/, "");
}

function embedded() {
  return window.VOX_VIEWER_EMBEDDED || { manifests: {}, vox: {}, images: {} };
}

function embeddedManifest(path) {
  const key = normalizePath(path);
  return embedded().manifests[key] || embedded().manifests[`/${key}`] || null;
}

function embeddedVox(path) {
  const key = normalizePath(path);
  return embedded().vox[key] || embedded().vox[`/${key}`] || null;
}

function embeddedImage(path) {
  const key = normalizePath(path);
  return embedded().images?.[key] || embedded().images?.[`/${key}`] || null;
}

function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

async function fetchJsonWithEmbeddedFallback(path) {
  const local = embeddedManifest(path);
  try {
    const response = await fetch(path);
    if (response.ok) {
      return response.json();
    }
  } catch {
    // File URLs and blocked local fetches use the embedded payload below.
  }
  if (local) {
    return local;
  }
  throw new Error(`Failed to load ${path}`);
}

async function fetchVoxWithEmbeddedFallback(path) {
  const local = embeddedVox(path);
  try {
    const response = await fetch(`/${normalizePath(path)}`);
    if (response.ok) {
      return response.arrayBuffer();
    }
  } catch {
    // File URLs and blocked local fetches use the embedded payload below.
  }
  if (local) {
    return base64ToArrayBuffer(local);
  }
  throw new Error(`Failed to load ${path}`);
}

async function loadModel(asset) {
  state.currentAsset = asset;
  const buffer = await fetchVoxWithEmbeddedFallback(asset.path);
  state.currentModel = parseVox(buffer);
  updateInfo();
  renderAssetList();
  fitZoom();
  render();
}

function fitZoom() {
  if (!state.currentModel) {
    return;
  }
  const { width, height } = cssSize();
  const frame = modelFrame(state.currentModel);
  const maxDim = Math.max(frame.width, frame.height, frame.depth);
  state.zoom = Math.max(8, Math.min(42, Math.min(width, height) / (maxDim * 2.0)));
}

function renderAssetList() {
  const dataset = state.datasets.get(state.currentDataset);
  assetList.innerHTML = "";
  if (!dataset) {
    return;
  }

  for (const asset of dataset.assets) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "asset-button";
    if (state.currentAsset && state.currentAsset.path === asset.path) {
      button.classList.add("active");
    }
    const size = Array.isArray(asset.size) ? asset.size.join("x") : "";
    button.innerHTML = `<span>${asset.name}</span><small>${size}</small>`;
    button.addEventListener("click", () => {
      loadModel(asset).catch(showError);
    });
    assetList.appendChild(button);
  }
}

function showError(error) {
  console.error(error);
  assetName.textContent = "Load failed";
  assetObserved.textContent = error.message;
}

async function loadDataset(datasetId) {
  state.currentDataset = datasetId;
  const dataset = state.datasets.get(datasetId);
  if (!dataset) {
    return;
  }
  renderAssetList();
  if (dataset.assets.length > 0) {
    await loadModel(dataset.assets[0]);
  }
}

async function init() {
  for (const dataset of DATASETS) {
    const option = document.createElement("option");
    option.value = dataset.id;
    option.textContent = dataset.name;
    datasetSelect.appendChild(option);
  }

  for (const dataset of DATASETS) {
    const assets = await fetchJsonWithEmbeddedFallback(dataset.manifest);
    state.datasets.set(dataset.id, { ...dataset, assets });
  }

  datasetSelect.value = state.currentDataset;
  datasetSelect.addEventListener("change", () => {
    loadDataset(datasetSelect.value).catch(showError);
  });

  resetViewButton.addEventListener("click", () => {
    state.yaw = -Math.PI / 4;
    state.pitch = -0.55;
    fitZoom();
    render();
  });

  infoToggle.addEventListener("click", () => {
    setInfoCollapsed(!state.infoCollapsed);
  });

  setInfoCollapsed(state.infoCollapsed);
  applyLayoutVars();
  await loadDataset(state.currentDataset);
  resizeCanvas();
}

canvas.addEventListener("pointerdown", (event) => {
  state.dragging = true;
  state.lastX = event.clientX;
  state.lastY = event.clientY;
  canvas.setPointerCapture(event.pointerId);
  canvas.classList.add("dragging");
});

canvas.addEventListener("pointermove", (event) => {
  if (!state.dragging) {
    return;
  }
  const dx = event.clientX - state.lastX;
  const dy = event.clientY - state.lastY;
  state.lastX = event.clientX;
  state.lastY = event.clientY;
  state.yaw = wrapAngle(state.yaw - dx * 0.01);
  state.pitch = wrapAngle(state.pitch + dy * 0.008);
  render();
});

canvas.addEventListener("pointerup", (event) => {
  state.dragging = false;
  canvas.releasePointerCapture(event.pointerId);
  canvas.classList.remove("dragging");
});

canvas.addEventListener("pointercancel", () => {
  state.dragging = false;
  canvas.classList.remove("dragging");
});

canvas.addEventListener("wheel", (event) => {
  event.preventDefault();
  const factor = Math.exp(-event.deltaY * 0.001);
  state.zoom = Math.max(4, Math.min(72, state.zoom * factor));
  render();
}, { passive: false });

leftResize.addEventListener("pointerdown", (event) => {
  startLayoutResize("left", event);
});

rightResize.addEventListener("pointerdown", (event) => {
  startLayoutResize("reference", event);
});

window.addEventListener("pointermove", updateLayoutResize);
window.addEventListener("pointerup", finishLayoutResize);
window.addEventListener("pointercancel", finishLayoutResize);

window.addEventListener("resize", () => {
  applyLayoutVars();
});

init().catch(showError);
