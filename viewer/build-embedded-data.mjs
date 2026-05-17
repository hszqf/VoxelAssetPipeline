import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, relative, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const examplesRoot = resolve(root, "examples");

const payload = { datasets: [], manifests: {}, vox: {}, images: {} };

function toPosix(path) {
  return path.replace(/\\/g, "/");
}

function normalizeKey(path) {
  return toPosix(path).replace(/^\/+/, "");
}

function titleCaseBatchName(name) {
  return name
    .replace(/[_-]+/g, " ")
    .replace(/\b[a-z]/g, (char) => char.toUpperCase());
}

function readJsonIfExists(path) {
  if (!existsSync(path)) {
    return {};
  }
  return JSON.parse(readFileSync(path, "utf8"));
}

function discoverManifests() {
  if (!existsSync(examplesRoot)) {
    return [];
  }

  return readdirSync(examplesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => resolve(examplesRoot, entry.name, "manifest.json"))
    .filter((manifestPath) => existsSync(manifestPath))
    .sort((a, b) => dirname(a).localeCompare(dirname(b), "en"));
}

const datasets = discoverManifests().map((absoluteManifestPath) => {
  const batchDir = dirname(absoluteManifestPath);
  const batchName = basename(batchDir);
  const manifestPath = normalizeKey(relative(root, absoluteManifestPath));
  const manifest = JSON.parse(readFileSync(resolve(root, manifestPath), "utf8"));
  const metadata = readJsonIfExists(resolve(batchDir, "dataset.json"));
  const firstAsset = manifest.find(Boolean) || {};
  const id = metadata.id || batchName.replace(/[_\s]+/g, "-").toLowerCase();
  const name = metadata.name || titleCaseBatchName(batchName);
  const cellResolution = metadata.cellResolution || firstAsset.cell_resolution || 64;

  return {
    id,
    name,
    manifest: `/${manifestPath}`,
    cellResolution,
    order: Number.isFinite(metadata.order) ? metadata.order : 1000,
    manifestData: manifest,
  };
});

datasets.sort((a, b) => a.order - b.order || a.name.localeCompare(b.name, "en"));

for (const dataset of datasets) {
  const manifestPath = normalizeKey(dataset.manifest);
  const manifest = dataset.manifestData;
  payload.datasets.push({
    id: dataset.id,
    name: dataset.name,
    manifest: dataset.manifest,
    cellResolution: dataset.cellResolution,
  });
  payload.manifests[manifestPath] = manifest;
  payload.manifests[`/${manifestPath}`] = manifest;

  for (const asset of manifest) {
    const key = normalizeKey(asset.path);
    payload.vox[key] = readFileSync(resolve(root, key)).toString("base64");
    payload.vox[`/${key}`] = payload.vox[key];

    const imagePaths = new Set();
    if (asset.source_image) imagePaths.add(asset.source_image);
    if (Array.isArray(asset.reference_views)) {
      for (const view of asset.reference_views) {
        if (view.path) imagePaths.add(view.path);
      }
    }
    for (const imagePath of imagePaths) {
      const imageKey = normalizeKey(imagePath);
      if (!payload.images[imageKey]) {
        payload.images[imageKey] = readFileSync(resolve(root, imageKey)).toString("base64");
        payload.images[`/${imageKey}`] = payload.images[imageKey];
      }
    }
  }
}

writeFileSync(resolve(import.meta.dirname, "embedded-data.js"), `window.VOX_VIEWER_EMBEDDED = ${JSON.stringify(payload)};\n`, "utf8");
console.log(`Wrote viewer/embedded-data.js with ${payload.datasets.length} datasets`);
