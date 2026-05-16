import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const manifests = [
  "examples/design_sheet_trial/manifest.json",
  "examples/quick_trial/manifest.json",
];

const payload = { manifests: {}, vox: {}, images: {} };

for (const manifestPath of manifests) {
  const manifest = JSON.parse(readFileSync(resolve(root, manifestPath), "utf8"));
  payload.manifests[manifestPath] = manifest;
  payload.manifests[`/${manifestPath}`] = manifest;

  for (const asset of manifest) {
    const key = asset.path.replace(/\\/g, "/").replace(/^\/+/, "");
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
      const imageKey = imagePath.replace(/\\/g, "/").replace(/^\/+/, "");
      if (!payload.images[imageKey]) {
        payload.images[imageKey] = readFileSync(resolve(root, imageKey)).toString("base64");
        payload.images[`/${imageKey}`] = payload.images[imageKey];
      }
    }
  }
}

writeFileSync(resolve(import.meta.dirname, "embedded-data.js"), `window.VOX_VIEWER_EMBEDDED = ${JSON.stringify(payload)};\n`, "utf8");
console.log("Wrote viewer/embedded-data.js");
