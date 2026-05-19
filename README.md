# VoxelAssetPipeline

Standalone workflow for generating, validating, and reviewing small voxel game assets before they are integrated into a game project.

<p align="center">
  <img src="examples/design_sheet_trial/preview.png" alt="Voxel asset preview grid" width="100%">
</p>

## What It Does

VoxelAssetPipeline turns an approved visual reference into `.vox` assets with repeatable review steps:

- approve style first with `Front 3/4 design + Back 3/4 design`, then generate a separate `Side / Front / Top` orthographic sheet
- build small MagicaVoxel-compatible `.vox` files
- render generated `Icon / Front 3/4 / Side / Front / Top` review images
- run structural checks such as `single_connected_component` and `floating_component_sizes`
- review everything in a static browser viewer that also works from `file://`
- optionally apply a game adapter, such as LittleWorld Unity prefab export

## Sources First

The first artifact should be a style reference for exactly one asset: `Front 3/4 design + Back 3/4 design`. For directional assets such as animals, this removes the common front/back ambiguity that made side-back icons easy to misread.

This first style reference must come from a user-provided raster image or an image-generation model. Do not use script-rendered `VoxelModel`, `.vox`, viewer, canvas, SVG, or projection output as the design reference; those are review artifacts after the design source has been approved.

After the style reference is approved, ask only for generated asset dimensions and the three-view panel grid size if they are not already provided. Propose a default asset dimension from the approved style reference, written as `X length x Y height x Z depth`; if there is no better estimate, use `32 x 32 x 32`. Ask whether to use the default `64 x 64` Side/Front/Top panel grid.

Then generate a separate orthographic sheet containing only `registered Side grid + registered Front grid + registered Top grid`, defaulting to `64 x 64` per panel. The left/front-back style views do not participate in occupied-cell measurement. Side, Front, and Top must show visible, countable grid guides, a bounding frame, and shared orthographic registration. The three-view grid lines must be drawn on the top layer above the asset art, so the grid remains visible across the silhouette. The panels are measurement guides for the source sheet, not game cells. Production prompts should be filled from `codex-skills/voxel-generation/references/style_reference_prompt_template.md` and `codex-skills/voxel-generation/references/source_sheet_prompt_template.md`.

After orthographic generation, run the PNG source-sheet checker and report the grid, bbox, and registration self-check before asking for approval. Side, Front, and Top must behave like a registered blueprint: Side length matches Top length, Front width matches Top width, Side/Front height and ground baseline match, and major landmarks line up. If the generated sheet is out of tolerance, has a clearly wrong grid, or is separately centered, do not silently regenerate; report the failed measurements first, then regenerate under the confirmed user specification or revise that specification with the user.

If an AI/user orthographic sheet has the right design but noisy or uneven grid art, normalize it with `clean-source-sheet` before voxel work. The cleaner detects the original drawn grid lines, cuts cells by those source lines, centers the source cells into the requested clean grid, and chooses each output cell color by the most frequent raw non-background RGB bucket inside that original cell. Do not redraw by semantics, merge palette meanings, stretch a view, or use voxel/viewer output as cleanup input.

Script-rendered sheets like the dog example below are deterministic review artifacts from one `VoxelModel`; they prove geometry after approval, but they should not be used as the first design source.

<p align="center">
  <img src="examples/dog_trial/reference_dog_icon_three_view_clean.png" alt="Dog source sheet with icon, front three-quarter, side, front, and top views" width="100%">
</p>

Only after the orthographic source sheet is approved should the pipeline write `.vox` files.

## Review Gallery

| Generated assets | Pipeline reference |
| --- | --- |
| <img src="examples/quick_trial/preview.png" alt="Quick trial generated voxel assets" width="100%"> | <img src="examples/quick_trial/reference_quick_trial_pipeline.png" alt="Quick trial reference views" width="100%"> |


## Viewer

Open the static viewer directly:

```text
viewer/index.html
```

If a browser blocks local file access, run the bundled static server:

```powershell
node viewer/server.mjs
```

Then open:

```text
http://127.0.0.1:5177/viewer/index.html
```

The Reference pane shows `Source` first, followed by generated `Icon / Front 3/4 / Side / Front / Top` views.

## Adding a Batch

Create a directory under `examples/` with a `manifest.json`:

```text
examples/missing_batch_01/manifest.json
```

Then rebuild the embedded viewer payload:

```powershell
python voxel_pipeline.py build-viewer-data
```

The viewer scans `examples/*/manifest.json` automatically. You do not need to edit `viewer/app.js` when adding a new batch.

Optional display metadata can be added next to the manifest:

```json
{
  "id": "missing-batch-01",
  "name": "Missing batch 01",
  "cellResolution": 64,
  "order": 100
}
```

## Commands

Run from the repository root:

```powershell
python voxel_pipeline.py generate-design-sheet
python voxel_pipeline.py check-design-sheet

python voxel_pipeline.py generate-quick-trial
python voxel_pipeline.py check-quick-trial

python voxel_pipeline.py generate-dog-trial
python voxel_pipeline.py check-dog-trial

python voxel_pipeline.py generate-horse-trial
python voxel_pipeline.py check-horse-trial

python voxel_pipeline.py check-source-sheet `
  --image "<source-sheet.png>" `
  --asset cow `
  --side 40x32 `
  --front 20x32 `
  --top 40x20 `
  --tolerance 4

python voxel_pipeline.py clean-source-sheet `
  --image "<ai-source-sheet.png>" `
  --asset cow `
  --grid-size 32 `
  --bucket-size 8 `
  --out "<clean-source-sheet.png>" `
  --overlay-out "<gridline-overlay.png>" `
  --json-out "<clean-source-cells.json>"

python voxel_pipeline.py build-viewer-data
```

Optional LittleWorld adapter:

```powershell
python voxel_pipeline.py apply-littleworld --project "E:\AI Projects\LittleWorld"
```

## Workflow

1. Generate or provide a style reference with `Front 3/4 design + Back 3/4 design`.
2. Approve style, direction, colors, and rough silhouette without measuring occupied cells.
3. Confirm generated asset dimensions and the three-view panel grid size, defaulting to 64x64.
4. Generate a separate orthographic sheet with `registered Side grid + registered Front grid + registered Top grid`.
5. Run `check-source-sheet` on the orthographic PNG.
6. Reject or regenerate it if Side/Front/Top lack valid grid guides, bounding frames, consistent scale, or shared orthographic registration.
7. If the design is good but grid detection is noisy, run `clean-source-sheet`, keep the original plus JSON/overlay evidence, then rerun `check-source-sheet`.
8. Stop for human approval of occupied proportion and landmark alignment.
9. Build `.vox` assets from the approved sheet.
10. Render source and generated reference views.
11. Run validators.
12. Rebuild `viewer/embedded-data.js`.
13. Inspect assets in `viewer/index.html`.
14. Apply a project adapter only after approval.

## Codex Skill

This repo includes a distributable Codex skill at:

```text
codex-skills/voxel-generation
```

Git does not install Codex skills automatically. After cloning, install it on Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_codex_skill.ps1
```

The installer copies the skill to:

```text
%USERPROFILE%\.codex\skills\voxel-generation
```

Restart Codex or refresh the skill list after installing. The skill appears as `体素生成` and can be invoked with `$voxel-generation`.

## Repository Map

```text
adapters/              Game-project integration adapters
codex-skills/          Distributable Codex skill package
docs/                  Workflow notes
examples/              Generated sample assets, manifests, and review images
scripts/               Utility scripts
viewer/                Static voxel review UI
voxel_asset_pipeline/  Core model, render, VOX, and validation helpers
workflows/             Asset-family generation and check scripts
```
