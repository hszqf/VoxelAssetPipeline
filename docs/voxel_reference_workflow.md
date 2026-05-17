# Voxel Reference Workflow

The first approved reference must be a design image, not a voxel render produced by this pipeline.

Default source reference format:

```text
Front 3/4 design | Back 3/4 design | Side 64-grid | Front 64-grid | Top 64-grid
```

Use one raster image for exactly one asset. It contains the front and back three-quarter design views plus three registered orthographic design views. The Side/Front/Top views must already include visible 64x64 guides, a bounding cell frame, and shared coordinate registration. These guides are part of source approval, not a post-voxel review overlay.

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
2. Before prompting, confirm `game_cells`, target occupied bounds, and tolerance with the user, such as `cow: about 40w x 32h x 20d inside one 64-cell frame, tolerance +/-4`.
3. Fill the skill prompt template from the confirmed contract; do not improvise prompt structure.
4. After generation, run `python voxel_pipeline.py check-source-sheet` when the source sheet is available as a PNG.
5. Estimate any remaining visual bbox or landmark issues in Side, Front, and Top and write a bbox plus registration self-check report.
6. Reject or regenerate it if Side/Front/Top do not include visible 64-cell guides, a bounding frame, consistent scale, registered axes, or the confirmed occupied bounds.
7. Do not silently regenerate. Report failed bbox or registration measurements before retrying or ask the user to revise the scale contract.
8. Stop for approval before creating voxel geometry or writing `.vox`.
9. Build the voxel model from the approved sheet.
10. Render generated review views: `Icon`, `Front 3/4`, `Side`, `Front`, and `Top`.
11. Run structural checks, especially `single_connected_component` and `floating_component_sizes`.
12. Rebuild `viewer/embedded-data.js`.
13. Review in `viewer/index.html`; the Reference pane should show `Source` first, followed by generated `Icon / Front 3/4 / Side / Front / Top`.

Single-cell scale guide:

| Tier | Typical occupied max dimension inside 64 | Examples |
| --- | --- | --- |
| tiny | 8-16 cells | flower, shell, pickup |
| small | 16-28 cells | frog, small dog, rock cluster |
| medium | 28-44 cells | cow, deer, wolf, medium prop |
| large | 44-56 cells | horse, small tree, large creature |
| full-cell | 56-64 cells | block, full-cell obstacle, wall segment |

AI prompt requirements:

- Request exactly one asset in one sheet with `Front 3/4 design | Back 3/4 design | registered Side 64-grid | registered Front 64-grid | registered Top 64-grid`.
- Use `codex-skills/voxel-generation/references/source_sheet_prompt_template.md` as the production prompt template.
- Require visible 64x64 grid guides and bounding cell frames on Side, Front, and Top.
- Keep Side, Front, and Top at the same scale.
- State concrete occupied bounds inside the 64x64 cell; small objects should leave visible empty space.
- Include front/back direction cues for animals and characters.
- Require registered orthographic axes: Side uses X length horizontally and Y height vertically; Front uses Z width/depth horizontally and Y height vertically; Top uses X length horizontally and Z width/depth vertically.
- Require the same front/head direction between Side and Top.
- Forbid colored axes, colored dashed baselines, measurement arrows/brackets, and dimension numbers inside grid panels.
- For batches, repeat this source approval loop one asset at a time.

PNG source-sheet checker:

```powershell
python voxel_pipeline.py check-source-sheet `
  --image "<source-sheet.png>" `
  --asset cow `
  --side 40x32 `
  --front 20x32 `
  --top 40x20 `
  --tolerance 4 `
  --json-out "<source-sheet-report.json>"
```

The checker detects the three orthographic grid panels, estimates real silhouette bboxes, checks target tolerance, flags colored guide annotations, checks Top length orientation, and checks basic Side/Front/Top registration. If auto frame detection fails, pass explicit `--side-frame x,y,w,h --front-frame x,y,w,h --top-frame x,y,w,h`.

BBox and registration self-check report:

```text
Scale contract: cow, game_cells=[1,1,1], target side 40w x 32h, top 40w x 20d, tolerance +/-4
Observed: side 54w x 42h, front 31w x 44h, top 48w x 29d
Registration: FAIL. Side length does not match Top length; Side/Front height does not match; Top is separately centered.
Result: FAIL. The cow is too large and not registered. Report these failures, then retry with stronger empty-space, 40x32x20 bounds, and registered axes.
```

Orthographic registration rules:

- Side, Front, and Top must behave like a blueprint registered to one coordinate system, not three separately centered illustrations.
- Side length must match Top length; Front width must match Top width; Side height must match Front height.
- Side and Front must share a ground baseline.
- Body center, front/head extent, back/tail extent, legs, ears/horns, wings, handles, and major markings must line up across views.
- AI-drawn grid art is only a design reference. After approval, generated review grids must come from one `VoxelModel` so the projections are deterministic.

Viewer dataset registration:

- Put each review batch under `examples/<batch_name>/manifest.json`.
- Run `python voxel_pipeline.py build-viewer-data`.
- `viewer/build-embedded-data.mjs` scans `examples/*/manifest.json` and writes `window.VOX_VIEWER_EMBEDDED.datasets`.
- `viewer/app.js` builds the Set dropdown from the embedded dataset metadata.
- Do not add batch names manually to `viewer/app.js`.
- Add optional `examples/<batch_name>/dataset.json` only when the displayed name, id, cell resolution, or order needs to be overridden.

If the source sheet contains multiple assets, split the batch and regenerate one source sheet per asset. If a script-rendered voxel draft was used as the first source image, discard it and restart from the design-source step. If the AI source sheet lacks Side/Front/Top 64-grid guides or registered orthographic axes, regenerate it before voxel work. If bbox or registration self-check fails, report the failed measurements before retrying; do not silently auto-regenerate. Do not patch the model forward; errors such as duplicated limbs usually come from skipping the design-source gate.

For animals and character assets:

- Treat top view as authoritative for back silhouette and markings.
- Add or inspect `Front 3/4` when the asset has a face, snout, chest, or other direction-specific front detail.
- Do not add a raised back patch unless it is visible in side and top views.
- Prefer flat, connected body volumes before adding decorative color variation.
