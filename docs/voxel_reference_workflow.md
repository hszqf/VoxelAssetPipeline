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
2. Before prompting, confirm `game_cells`, target occupied bounds, and tolerance with the user, such as `cow: about 40w x 32h x 20d inside one 64-cell frame, tolerance ±4`.
3. After generation, estimate the visible bounding box in Side, Front, and Top and write a self-check report.
4. Reject or regenerate it if Side/Front/Top do not include visible 64-cell guides, a bounding frame, consistent scale, or the confirmed occupied bounds.
5. Do not silently regenerate. Report failed bbox measurements before retrying or ask the user to revise the scale contract.
6. Stop for approval before creating voxel geometry or writing `.vox`.
7. Build the voxel model from the approved sheet.
8. Render generated review views: `Icon`, `Front 3/4`, `Side`, `Front`, and `Top`.
9. Run structural checks, especially `single_connected_component` and `floating_component_sizes`.
10. Rebuild `viewer/embedded-data.js`.
11. Review in `viewer/index.html`; the Reference pane should show `Source` first, followed by generated `Icon / Front 3/4 / Side / Front / Top`.

Single-cell scale guide:

| Tier | Typical occupied max dimension inside 64 | Examples |
| --- | --- | --- |
| tiny | 8-16 cells | flower, shell, pickup |
| small | 16-28 cells | frog, small dog, rock cluster |
| medium | 28-44 cells | cow, deer, wolf, medium prop |
| large | 44-56 cells | horse, small tree, large creature |
| full-cell | 56-64 cells | block, full-cell obstacle, wall segment |

AI prompt requirements:

- Request exactly one asset in one sheet with `Front 3/4 design | Back 3/4 design | Side 64-grid | Front 64-grid | Top 64-grid`.
- Require visible 64x64 grid guides and bounding cell frames on Side, Front, and Top.
- Keep Side, Front, and Top at the same scale.
- State concrete occupied bounds inside the 64x64 cell; small objects should leave visible empty space.
- Include front/back direction cues for animals and characters.
- For batches, repeat this source approval loop one asset at a time.

BBox self-check report:

```text
Scale contract: cow, game_cells=[1,1,1], target side 40w x 32h, top 40w x 20d, tolerance ±4
Observed: side 54w x 42h, front 31w x 44h, top 48w x 29d
Result: FAIL. The cow is too large for the medium single-cell budget. Regenerating with stronger empty-space and 40x32x20 bounds.
```

Viewer dataset registration:

- Put each review batch under `examples/<batch_name>/manifest.json`.
- Run `python voxel_pipeline.py build-viewer-data`.
- `viewer/build-embedded-data.mjs` scans `examples/*/manifest.json` and writes `window.VOX_VIEWER_EMBEDDED.datasets`.
- `viewer/app.js` builds the Set dropdown from the embedded dataset metadata.
- Do not add batch names manually to `viewer/app.js`.
- Add optional `examples/<batch_name>/dataset.json` only when the displayed name, id, cell resolution, or order needs to be overridden.

If the source sheet contains multiple assets, split the batch and regenerate one source sheet per asset. If a script-rendered voxel draft was used as the first source image, discard it and restart from the design-source step. If the AI source sheet lacks Side/Front/Top 64-grid guides, regenerate it before voxel work. If bbox self-check fails, report the failed measurements before retrying; do not silently auto-regenerate. Do not patch the model forward; errors such as duplicated limbs usually come from skipping the design-source gate.

For animals and character assets:

- Treat top view as authoritative for back silhouette and markings.
- Add or inspect `Front 3/4` when the asset has a face, snout, chest, or other direction-specific front detail.
- Do not add a raised back patch unless it is visible in side and top views.
- Prefer flat, connected body volumes before adding decorative color variation.
