---
name: voxel-generation
description: Generate voxel game assets / 体素素材 / 体素生成 from reference images, including first-step reference approval, one-sheet Icon/Front 3/4/Side/Front/Top references, proportional 64-cell voxel modeling, .vox export, review renders, structural checks, static viewer review, and optional project adapter integration. Use when the user needs 体素素材, voxel assets, .vox files, 小模型生成, or review generated voxel models.
---

# Voxel Generation

Use this skill when a user needs voxel game assets or `.vox` files.

## Required Workflow

1. Start with a raster reference image or generate one.
2. Default to one approved source sheet containing `Icon + Front 3/4 + Side + Front + Top` in a single image. Use multi-angle sheets only for exploration.
3. Stop after the first source sheet and wait for user confirmation before converting to `.vox`.
4. After confirmation, create voxel models at the agreed game-cell scale. Default: one game cell is `64 x 64 x 64`; small objects should occupy only their real proportion inside that cell.
5. Render per-asset review views: `Source`, `Icon`, `Front 3/4`, `Side`, `Front`, and `Top`.
6. Run structural validation. Every model must pass `single_connected_component`; `floating_component_sizes` must be empty. Do not rely only on visual inspection.
7. Update the static viewer data and ask the user to inspect assets one by one.
8. Only after user approval, run the project adapter to integrate assets into the game.

## Tool Project

Use the current workspace if it contains `voxel_pipeline.py`. If not, ask for the local `VoxelAssetPipeline` clone path.

Run the CLI from the project root:

```powershell
python voxel_pipeline.py generate-design-sheet
python voxel_pipeline.py check-design-sheet
python voxel_pipeline.py generate-quick-trial
python voxel_pipeline.py check-quick-trial
python voxel_pipeline.py generate-dog-trial
python voxel_pipeline.py check-dog-trial
python voxel_pipeline.py build-viewer-data
python voxel_pipeline.py apply-littleworld --project "E:\AI Projects\LittleWorld"
```

The static viewer is available at `viewer/index.html`. It should work from `file://`; use `node viewer/server.mjs` only when a browser blocks local file access.

## Review Rules

- Preserve scale relationships before detail. A tiny object should not fill the 64-cell frame.
- Treat the top view as authoritative for back silhouette, roof/canopy footprint, and markings.
- Do not add raised detail unless it is visible in the source sheet's side and top views.
- Prefer a connected hidden/back-side support voxel over isolated decorative voxels.
- Treat wings, fins, mushroom caps, and canopies as valid overhangs only when connected to the main model.
- If orientation is ambiguous, generate or request a source sheet with `Icon + Front 3/4 + Side + Front + Top` before `.vox` work.

## References

Read `references/workflow.md` when extending the pipeline, adding adapters, changing validation rules, or creating a new asset family.
