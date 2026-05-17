# VoxelAssetPipeline

Standalone workflow for generating, validating, and reviewing small voxel game assets before they are integrated into a game project.

<p align="center">
  <img src="examples/design_sheet_trial/preview.png" alt="Voxel asset preview grid" width="100%">
</p>

## What It Does

VoxelAssetPipeline turns an approved visual reference into `.vox` assets with repeatable review steps:

- start from a single source sheet: `Icon + Front 3/4 + Side + Front + Top`
- build small MagicaVoxel-compatible `.vox` files
- render generated `Icon / Front 3/4 / Side / Front / Top` review images
- run structural checks such as `single_connected_component` and `floating_component_sizes`
- review everything in a static browser viewer that also works from `file://`
- optionally apply a game adapter, such as LittleWorld Unity prefab export

## Source Sheet First

The first artifact should be a combined source sheet. For directional assets such as animals, `Front 3/4` removes the common front/back ambiguity that made side-back icons easy to misread.

<p align="center">
  <img src="examples/dog_trial/reference_dog_icon_three_view_clean.png" alt="Dog source sheet with icon, front three-quarter, side, front, and top views" width="100%">
</p>

Only after the source sheet is approved should the pipeline write `.vox` files.

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

## Commands

Run from the repository root:

```powershell
python voxel_pipeline.py generate-design-sheet
python voxel_pipeline.py check-design-sheet

python voxel_pipeline.py generate-quick-trial
python voxel_pipeline.py check-quick-trial

python voxel_pipeline.py generate-dog-trial
python voxel_pipeline.py check-dog-trial

python voxel_pipeline.py build-viewer-data
```

Optional LittleWorld adapter:

```powershell
python voxel_pipeline.py apply-littleworld --project "E:\AI Projects\LittleWorld"
```

## Workflow

1. Generate or provide a source sheet.
2. Stop for human approval of style, direction, silhouette, and scale.
3. Build `.vox` assets from the approved sheet.
4. Render source and generated reference views.
5. Run validators.
6. Rebuild `viewer/embedded-data.js`.
7. Inspect assets in `viewer/index.html`.
8. Apply a project adapter only after approval.

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
