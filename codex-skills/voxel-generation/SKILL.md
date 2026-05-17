---
name: voxel-generation
description: Generate voxel game assets / 体素素材 / 体素生成 from approved raster design references, including a hard first-step gate that forbids script-rendered voxel drafts as design references, one-asset-per-sheet Front 3/4 design/Back 3/4 design/Side 64-grid/Front 64-grid/Top 64-grid source sheets, automatic asset-name labels on reference/review images, proportional 64-cell voxel modeling, .vox export, review renders, structural checks, static viewer review, and optional project adapter integration. Use when the user needs 体素素材, voxel assets, .vox files, 小模型生成, AI voxel icon design references, or review generated voxel models.
---

# Voxel Generation

Use this skill when a user needs voxel game assets or `.vox` files.

## Required Workflow

1. Start with a real raster design reference from the user or an image-generation model. Do not use `VoxelModel`, `.vox`, canvas/SVG/PNG script rendering, or viewer screenshots as the first design reference.
2. Default to one approved AI source sheet for exactly one asset, containing `Front 3/4 design + Back 3/4 design + Side 64-grid + Front 64-grid + Top 64-grid` in a single image. The Side/Front/Top orthographic design views must already include visible 64x64 cell guides and a bounding cell frame.
3. Reject or regenerate the source sheet before asking for approval if the orthographic design views do not show the 64-cell guide, if the asset fills the whole 64x64 frame without intended scale, or if the Side/Front/Top views are not in the same scale system.
4. Stop after the first valid source sheet and wait for user confirmation before creating voxel geometry, `.vox`, manifests, or viewer data.
5. After confirmation, create voxel models at the agreed game-cell scale. Default: one game cell is `64 x 64 x 64`; small objects should occupy only their real proportion inside that cell.
6. Render per-asset review views: `Source`, `Icon`, `Front 3/4`, `Side`, `Front`, and `Top`. Every generated source sheet, multi-row reference sheet, and projection review image must include the asset's model/manifest name in the upper-left corner of its row.
7. Run structural validation. Every model must pass `single_connected_component`; `floating_component_sizes` must be empty. Do not rely only on visual inspection.
8. Update the static viewer data and ask the user to inspect assets one by one.
9. Only after user approval, run the project adapter to integrate assets into the game.

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
- Generate and approve one asset per source sheet. Do not ask an image model for multiple animals, props, or characters in one source sheet.
- Treat source references and voxel review renders as different artifact classes. Script-rendered voxel images are allowed only after the design source is approved.
- Treat the source sheet's Side/Front/Top 64-grid views as design requirements, not post-voxel review extras.
- AI image prompts must explicitly request visible 64x64 guides, a bounding cell frame, and the asset's intended occupied proportion inside the cell.
- Add asset-name labels automatically during rendering. Use the model/manifest name such as `dog_golden`, not a subjective display description.
- Treat the top view as authoritative for back silhouette, roof/canopy footprint, and markings.
- Do not add raised detail unless it is visible in the source sheet's side and top views.
- Prefer a connected hidden/back-side support voxel over isolated decorative voxels.
- Treat wings, fins, mushroom caps, and canopies as valid overhangs only when connected to the main model.
- If orientation is ambiguous, generate or request a source sheet with `Front 3/4 design + Back 3/4 design + Side 64-grid + Front 64-grid + Top 64-grid` before `.vox` work.

## References

Read `references/workflow.md` when extending the pipeline, adding adapters, changing validation rules, or creating a new asset family.
