# Voxel Reference Workflow

The first approved reference must be a design image, not a voxel render produced by this pipeline.

Default source reference format:

```text
Front 3/4 design | Back 3/4 design | Side 64-grid | Front 64-grid | Top 64-grid
```

Use one raster image for exactly one asset. It contains the front and back three-quarter design views plus three orthographic design views. The Side/Front/Top views must already include visible 64x64 guides and a bounding cell frame. These guides are part of source approval, not a post-voxel review overlay.

Allowed first-step references:

- user-provided raster image
- image-generation model output
- edited raster design image based on approved user intent

Forbidden as first-step references:

- `VoxelModel` output
- `.vox` render output
- viewer screenshots
- script-rendered canvas/SVG/PNG voxel drafts
- generated projections from an unapproved voxel model

Workflow:

1. Generate or provide the combined source sheet using a real raster design source.
2. Reject or regenerate it if Side/Front/Top do not include visible 64-cell guides, a bounding frame, and consistent scale.
3. Stop for approval before creating voxel geometry or writing `.vox`.
4. Build the voxel model from the approved sheet.
5. Render generated review views: `Icon`, `Front 3/4`, `Side`, `Front`, and `Top`.
6. Run structural checks, especially `single_connected_component` and `floating_component_sizes`.
7. Rebuild `viewer/embedded-data.js`.
8. Review in `viewer/index.html`; the Reference pane should show `Source` first, followed by generated `Icon / Front 3/4 / Side / Front / Top`.

AI prompt requirements:

- Request exactly one asset in one sheet with `Front 3/4 design | Back 3/4 design | Side 64-grid | Front 64-grid | Top 64-grid`.
- Require visible 64x64 grid guides and bounding cell frames on Side, Front, and Top.
- Keep Side, Front, and Top at the same scale.
- Show intended occupied proportion inside the 64x64 cell; small objects should leave visible empty space.
- Include front/back direction cues for animals and characters.
- For batches, repeat this source approval loop one asset at a time.

Viewer dataset registration:

- Put each review batch under `examples/<batch_name>/manifest.json`.
- Run `python voxel_pipeline.py build-viewer-data`.
- `viewer/build-embedded-data.mjs` scans `examples/*/manifest.json` and writes `window.VOX_VIEWER_EMBEDDED.datasets`.
- `viewer/app.js` builds the Set dropdown from the embedded dataset metadata.
- Do not add batch names manually to `viewer/app.js`.
- Add optional `examples/<batch_name>/dataset.json` only when the displayed name, id, cell resolution, or order needs to be overridden.

If the source sheet contains multiple assets, split the batch and regenerate one source sheet per asset. If a script-rendered voxel draft was used as the first source image, discard it and restart from the design-source step. If the AI source sheet lacks Side/Front/Top 64-grid guides, regenerate it before voxel work. Do not patch the model forward; errors such as duplicated limbs usually come from skipping the design-source gate.

For animals and character assets:

- Treat top view as authoritative for back silhouette and markings.
- Add or inspect `Front 3/4` when the asset has a face, snout, chest, or other direction-specific front detail.
- Do not add a raised back patch unless it is visible in side and top views.
- Prefer flat, connected body volumes before adding decorative color variation.
