---
name: voxel-generation
description: Generate voxel game assets / 体素素材 / 体素生成 from approved raster design references, including a hard first-step gate that forbids script-rendered voxel drafts as design references, user-confirmed scale budgets, one-asset-per-sheet Front 3/4 design/Back 3/4 design/registered Side 64-grid/Front 64-grid/Top 64-grid source sheets, mandatory bounding-box and orthographic registration self-check reports before approval, automatic asset-name labels on reference/review images, proportional 64-cell voxel modeling, .vox export, deterministic review renders, structural checks, static viewer review, and optional project adapter integration. Use when the user needs 体素素材, voxel assets, .vox files, 小模型生成, AI voxel icon design references, or review generated voxel models.
---

# Voxel Generation

Use this skill when a user needs voxel game assets or `.vox` files.

## Required Workflow

1. Start with a real raster design reference from the user or an image-generation model. Do not use `VoxelModel`, `.vox`, canvas/SVG/PNG script rendering, or viewer screenshots as the first design reference.
2. Before prompting for the source sheet, establish a scale contract with the user: target `game_cells`, intended occupied voxel bounds, and tolerance inside the guide, such as `cow: about 40w x 32h x 20d inside one 64-cell frame, tolerance +/-4 cells`.
3. Use `references/source_sheet_prompt_template.md` to fill a concrete prompt from the confirmed scale contract. Do not freehand source-sheet prompts.
4. Default to one approved AI source sheet for exactly one asset, containing `Front 3/4 design + Back 3/4 design + registered Side 64-grid + registered Front 64-grid + registered Top 64-grid` in a single image. The Side/Front/Top orthographic design views must already include visible 64x64 cell guides, a bounding cell frame, and shared coordinate registration.
5. Require orthographic registration in the source sheet: Side maps length X vs height Y, Front maps width/depth Z vs height Y, and Top maps length X vs width/depth Z. The views must share front/head direction, ground baseline, body center, height, length, width, and major feature positions such as legs, head, tail, ears, horns, wings, handles, or markings.
6. Do not ask the AI to draw colored axes, dimension arrows, brackets, or numeric measurement labels inside grid panels. These confuse the source checker and can hide that the real silhouette exceeds the contract.
7. After generation, run `python voxel_pipeline.py check-source-sheet` with the confirmed Side/Front/Top target dimensions. Include the JSON result in the source approval discussion.
8. Reject the source sheet before asking for approval if the checker fails, if the orthographic design views do not show the 64-cell guide, if the asset ignores the confirmed scale contract, if the asset fills the whole 64x64 frame without intent, if the Side/Front/Top views are not in the same scale system, or if the orthographic registration fails.
9. Do not silently regenerate. If the source sheet fails the bbox or registration self-check, tell the user the failed measurements/checks first, then regenerate only under the confirmed scale contract or ask for a revised scale contract. Failed sheets may be shown as failure evidence, but they are not approval candidates.
10. Stop after the first valid source sheet and wait for user confirmation before creating voxel geometry, `.vox`, manifests, or viewer data.
11. After confirmation, create voxel models at the agreed game-cell scale. Default: one game cell is `64 x 64 x 64`; assets should occupy only their declared proportion inside that cell.
12. After voxel geometry exists, render deterministic per-asset review views from the same `VoxelModel`: `Source`, `Icon`, `Front 3/4`, `Side`, `Front`, and `Top`. Every generated source sheet, multi-row reference sheet, and projection review image must include the asset's model/manifest name in the upper-left corner of its row.
13. Run structural validation. Every model must pass `single_connected_component`; `floating_component_sizes` must be empty. Do not rely only on visual inspection.
14. Update the static viewer data and ask the user to inspect assets one by one.
15. Only after user approval, run the project adapter to integrate assets into the game.

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
python voxel_pipeline.py check-source-sheet --image "<source-sheet.png>" --asset cow --side 40x32 --front 20x32 --top 40x20 --tolerance 4
python voxel_pipeline.py build-viewer-data
python voxel_pipeline.py apply-littleworld --project "E:\AI Projects\LittleWorld"
```

The static viewer is available at `viewer/index.html`. It should work from `file://`; use `node viewer/server.mjs` only when a browser blocks local file access.

## Review Rules

- Preserve scale relationships before detail. A tiny object should not fill the 64-cell frame.
- Confirm the occupied bounds before image generation. Prompt with concrete dimensions, not just "small" or "large"; if the user has not confirmed the scale contract, ask before generating.
- Prompt from `references/source_sheet_prompt_template.md`; do not improvise prompt structure for production source sheets.
- Run `check-source-sheet` after generation, then estimate/report any remaining visual issues. Do not ask for source approval until the checker and manual registration review pass.
- Never silently discard and regenerate a failed source sheet. Report the failed bbox and registration details, then either regenerate under the confirmed contract or ask the user to revise the contract.
- If the intended object is larger than one 64-cell frame, choose multi-cell `game_cells` before source generation instead of cramming it into one cell.
- Generate and approve one asset per source sheet. Do not ask an image model for multiple animals, props, or characters in one source sheet.
- Treat source references and voxel review renders as different artifact classes. Script-rendered voxel images are allowed only after the design source is approved.
- Treat the source sheet's Side/Front/Top 64-grid views as design requirements, not post-voxel review extras.
- AI image prompts must explicitly request visible 64x64 guides, a bounding cell frame, the asset's intended occupied bounds inside the cell, and registered orthographic axes.
- AI image prompts must explicitly forbid colored axes, colored baselines, measurement brackets, arrows, and dimension numbers inside grid panels.
- Default orthographic axes: Side uses X length horizontally and Y height vertically; Front uses Z width/depth horizontally and Y height vertically; Top uses X length horizontally and Z width/depth vertically. Front/head direction must be marked and consistent between Side and Top.
- Reject AI sheets where Side, Front, and Top are separately centered art panels instead of registered blueprint views. Side length must match Top length, Front width must match Top width, and Side/Front height plus ground baseline must match.
- Do not trust AI-drawn grid artwork as exact geometry. Use it only as the design approval reference; after approval, generate review grids from the actual `VoxelModel` so Side/Front/Top are deterministic projections of the same voxel coordinates.
- Add asset-name labels automatically during rendering. Use the model/manifest name such as `dog_golden`, not a subjective display description.
- Treat the top view as authoritative for back silhouette, roof/canopy footprint, and markings.
- Do not add raised detail unless it is visible in the source sheet's side and top views.
- Prefer a connected hidden/back-side support voxel over isolated decorative voxels.
- Treat wings, fins, mushroom caps, and canopies as valid overhangs only when connected to the main model.
- If orientation is ambiguous, generate or request a source sheet with `Front 3/4 design + Back 3/4 design + Side 64-grid + Front 64-grid + Top 64-grid` before `.vox` work.

## References

Read `references/workflow.md` when extending the pipeline, adding adapters, changing validation rules, or creating a new asset family.
