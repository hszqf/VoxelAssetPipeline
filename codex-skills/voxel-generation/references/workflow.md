# Voxel Asset Pipeline Workflow

Core invariant: style approval and orthographic source-sheet approval both happen before voxel geometry or `.vox` generation.

The source sheet must be a design reference, not a voxel draft rendered by this pipeline.

Default two-stage source format:

```text
Stage 1 style reference: Front 3/4 design | Back 3/4 design
Stage 2 setup: generated asset dimensions | three-view panel grid, default 64x64
Stage 3 orthographic sheet: registered Side grid | registered Front grid | registered Top grid
```

Use one asset per image. The style reference settles front/back identity, colors, silhouette, and distinctive features. The orthographic sheet is generated after style approval and contains only the registered Side/Front/Top design views. Side/Front/Top must include visible, countable 64x64 guides, a bounding cell frame, and shared coordinate registration. These guides are part of source approval, not a post-voxel review overlay.

Allowed first-step source references:

- user-provided raster image
- image-generation model output
- edited or composited raster design image based on user-approved design intent

Forbidden as first-step design references:

- output from `VoxelModel`
- `.vox` renders
- viewer screenshots
- canvas/SVG/PNG script drawings of a voxel draft
- generated orthographic projections from an unapproved voxel model

Script-rendered images are review artifacts only. They can be produced after the user approves a real design source and after voxel geometry exists.

Design source vs deterministic review:

- AI or user raster style references settle style, silhouette, and direction.
- AI or user raster orthographic sheets settle scale intent and approximate registered Side/Front/Top design.
- Script-rendered `VoxelModel` sheets prove exact geometry after approval. They are deterministic projections from one voxel coordinate set, like `dog_golden`; they are not valid first-step design sources.
- If an early image looks perfectly grid-registered because it was rendered from a script or voxel draft, treat it as a review artifact and restart the design-source gate.

User specification gate:

- Before generating the orthographic sheet, ask exactly two user-facing questions when they are not already provided: generated asset dimensions and three-view panel grid size.
- Always propose a default generated asset dimension inferred from the approved style reference, written as `X length x Y height x Z depth`. If there is no better estimate, use `32 x 32 x 32` as the fallback default.
- Ask whether to use the default `64 x 64` grid for each Side/Front/Top panel. Only ask for a different panel size if the proposed asset dimensions do not fit comfortably.
- Use an internal default tolerance, usually `+/-4 cells` or about `10%` of the target dimension. Do not ask about tolerance unless the user brings it up.
- Do not introduce `game_cells` or game-grid assumptions. This workflow is a generic voxel asset tool and must follow the user's requested specification.
- Do not ask for engine scale, split strategy, maximum bounding box, or other output constraints at this gate.
- Do not let a normal animal, prop, plant, or pickup fill the full 64x64 source guide unless the user intentionally requests a near-full-guide asset.
- If the object should be larger than the default `64 x 64` source guide, ask for a larger generated asset dimension and/or larger three-view panel grid before source generation.
- Reject source sheets where the asset ignores the declared bounds.

Generic 64-cell guide size hints:

| Tier | Typical occupied max dimension inside 64 | Examples |
| --- | --- | --- |
| tiny | 8-16 cells | flower, shell, pickup |
| small | 16-28 cells | frog, small dog, rock cluster |
| medium | 28-44 cells | cow, wolf, medium prop |
| large | 44-56 cells | cart, small tree, large creature |
| full-cell | 56-64 cells | block, full-cell obstacle, wall segment |

AI source prompt requirements:

- Ask for exactly one asset in one clean sheet.
- Fill `references/style_reference_prompt_template.md` for the style reference.
- Fill `references/source_sheet_prompt_template.md` for the orthographic sheet from the approved style reference, confirmed generated asset dimensions, and confirmed three-view panel grid size.
- Do not freehand production prompts.
- The style reference contains `Front 3/4 design | Back 3/4 design` only.
- The orthographic sheet contains registered `Side | Front | Top` grids only, defaulting to 64x64 per panel.
- Require visible grid guides and a clear bounding frame on Side, Front, and Top.
- Require the Side/Front/Top grid lines to be drawn on the top layer above the asset art, so the grid stays visible across the silhouette.
- Require the same scale across Side, Front, and Top.
- Require the asset to occupy its declared bounds inside the confirmed source guide, not fill the entire frame unless the user requested that.
- For small creatures, props, plants, and pickups, state that the object should use only a small portion of the cell while preserving empty space.
- Require direction cues in both Front 3/4 and Back 3/4 views for animals and characters.
- Require orthographic axes: Side uses X length horizontally and Y height vertically; Front uses Z width/depth horizontally and Y height vertically; Top uses X length horizontally and Z width/depth vertically.
- Mark the front/head direction and keep it consistent between Side and Top.
- Forbid colored axes, colored dashed baselines, dimension arrows, brackets, and numeric measurement labels inside grid panels. The checker measures the real silhouette; AI-written numbers are not trusted.

Blueprint source quality:

- Treat the orthographic source sheet as measurement input, not presentation art.
- Ask for flat blocky voxel-pixel blueprint art: simple solid color rectangles, crisp orthographic silhouettes, and low decoration.
- Explicitly forbid isometric or perspective views, soft shadows, cast shadows, gradients, glossy lighting, coordinate numbers, tick labels, legends, dimension text, arrows, and brackets.
- Prefer a smaller clean image with countable grid lines over a high-resolution polished render. Pixel resolution is less important than measurable 64-cell registration.
- If a source image looks good but checker sees the whole frame as object, it is usually too rendered: shadows, gradients, antialiasing, or noisy grid lines are contaminating bbox detection.

Orthographic registration gate:

- Do not accept Side, Front, and Top as three separately centered drawings. They must behave like a blueprint registered to one shared coordinate system.
- Side length must match Top length on X within tolerance.
- Front width must match Top width on Z within tolerance.
- Side height must match Front height on Y within tolerance.
- Side and Front must share the same ground baseline.
- Body center, head/front extent, back/tail extent, leg positions, ears/horns, wings, handles, major markings, and other structural landmarks must line up across the views.
- If the source sheet has a plausible style but failed registration, show it only as failure evidence. Do not ask for source approval and do not begin `.vox` work.

Source approval gate:

- Do not approve multi-asset source sheets. For batches, repeat the style and orthographic approval loop once per asset.
- Approve the style reference before generating orthographic views.
- Do not measure scale from `Front 3/4` or `Back 3/4`; they are style/direction inputs only.
- Do not ask for approval if Side/Front/Top lack visible grid guides, or if the asset art covers the grid lines instead of the grid being drawn on top.
- Before asking for approval, run the PNG source-sheet checker when the source sheet is available as a local PNG:

```powershell
python voxel_pipeline.py check-source-sheet --image "<source-sheet.png>" --asset cow --side 40x32 --front 20x32 --top 40x20 --tolerance 4 --json-out "<source-sheet-report.json>"
```

- The checker detects grid panels, reports approximate grid-line counts, estimates real silhouette bboxes, checks target tolerances, flags colored guide annotations, checks top orientation, and checks basic Side/Front/Top registration.
- If auto panel detection fails, pass explicit frame coordinates with `--side-frame x,y,w,h --front-frame x,y,w,h --top-frame x,y,w,h`.
- If colored-annotation checks fail because the asset itself is red/orange/blue/green, visually confirm that there are no colored axes, arrows, baselines, or dimension marks before using `--allow-colored-annotations`. Mention this as a checker false positive in the report.
- The checker is a hard gate for measurable failures, not a replacement for human visual review.
- Before asking for approval, estimate any remaining occupied bounding box or landmark issues in the Side, Front, and Top panels.
- Write a short bbox and registration self-check report: target bounds, observed Side/Front/Top bounds, tolerance, registration checks, and pass/fail.
- Do not approve if the asset's bounding box is much larger or smaller than the confirmed user specification.
- Do not approve if Side/Front/Top have inconsistent origins, separately centered silhouettes, mismatched height/length/width, inconsistent ground baseline, or contradictory landmark positions.
- Do not create `VoxelModel`, `.vox`, manifest, viewer data, or generated review renders before this gate passes.
- If the AI model omits the guides or changes scale between views, regenerate the source sheet with a stricter prompt.
- Do not silently regenerate a failed source sheet. Tell the user the failed measurements/checks first; then regenerate under the confirmed user specification, or ask for a revised specification when the target itself seems wrong.
- A cleaned/composited raster source is allowed only when it starts from an approved AI/user raster source and preserves the approved silhouette, colors, direction, landmarks, and user specification. Acceptable cleanup includes normalizing the 64-grid, separating panels, removing coordinate labels, and reducing shadows/noise so the checker can measure. Keep the failed original and JSON report as evidence. Do not create a cleaned source from `VoxelModel`, `.vox`, generated review renders, or viewer screenshots.

Example bbox and registration self-check:

```text
User specification: cow, generated asset 40 x 32 x 20, three-view panel grid 64 x 64, tolerance +/-4
Observed: side 54w x 42h, front 31w x 44h, top 48w x 29d
Registration: FAIL. Side length does not match Top length; Side/Front height does not match; Top is separately centered.
Result: FAIL. The cow is too large and not registered. Report these failures, then regenerate with stronger empty-space, 40x32x20 bounds, and registered axes.
```

Pipeline stages:

1. Style reference: generated by an image model or provided by the user, used to settle visual style, orientation, front/back identity, colors, and silhouette.
2. User specification: ask only for generated asset dimensions, with a default, and three-view panel grid size, default 64x64.
3. Orthographic source sheet: generated from the approved style reference and user specification, used to settle declared occupied bounds and Side/Front/Top registration.
4. Approval stop: do not write `.vox` until the user approves a checker-passing orthographic source sheet.
5. Voxel construction: convert into a structured `VoxelModel` array and write MagicaVoxel `.vox`.
6. Review renders: approved sources plus generated icon, front three-quarter, and side/front/top views inside the confirmed guide. The generated side/front/top views must come from the same `VoxelModel` coordinate set, not AI-drawn panels. Add the asset's model/manifest name in the upper-left corner of every generated source/review row.
7. Validation: user-requested size fit, domain-specific checks, `single_connected_component`, and `floating_component_sizes`.
8. Viewer: rebuild `viewer/embedded-data.js` so `viewer/index.html` works from `file://`; the Reference pane should show `Source` first, then generated `Icon / Front 3/4 / Side / Front / Top`.
9. Adapter: apply only after user approval.

When adding new assets, update:

- a generation workflow and its builder list
- a validation workflow with per-asset checks
- `examples/<batch_name>/manifest.json`
- optional `examples/<batch_name>/dataset.json` for display overrides
- project adapter mapping only when the game has a matching entity prefab

Do not manually register new batches in `viewer/app.js`. Run `python voxel_pipeline.py build-viewer-data`; the build script scans `examples/*/manifest.json` and emits dataset metadata for the viewer dropdown.

Reference and review image labels:

- Label every generated source sheet, multi-row reference sheet, and projection review image.
- Place the label in the upper-left corner of the asset row.
- Use the model/manifest name, for example `dog_golden` or `trial_rock_cluster`.
- Add labels in the renderer, not by manually editing output images.
- Keep labels outside the core silhouette as much as possible and avoid covering important structural details.

Failure handling:

- If the source sheet contains multiple assets, split the batch and regenerate one source sheet per asset.
- If the first source image was accidentally created by script-rendering a voxel draft, discard it as a design source.
- If the AI orthographic sheet lacks Side/Front/Top 64-grid guides or the grid-line count is clearly not 64x64, discard or regenerate it before voxel work.
- If the bbox or registration self-check fails, report the failed measurements/checks before retrying; do not silently auto-regenerate.
- If visual quality is correct but checker failure is caused by rendered shadows, antialiasing, panel detection, or colored asset false positives, either regenerate with stricter blueprint wording or create a cleaned raster source from the AI/user source under the cleanup rule above, then rerun the checker.
- Return to the design-source step and generate or request a proper raster design reference.
- Do not continue by patching the draft model; this hides anatomy and proportion errors such as duplicated legs.

Animal and character assets:

- Treat top view as authoritative for back silhouette and markings.
- Add or inspect `Front 3/4` when the asset has a face, snout, chest, or other direction-specific front detail.
- Do not add a raised back patch unless it is visible in side and top views.
- Prefer flat, connected body volumes before adding decorative color variation.
