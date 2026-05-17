# VoxelAssetPipeline

Standalone voxel asset workflow extracted from LittleWorld.

## Workflow

1. Generate or provide a first-step reference image.
2. Prefer a single source sheet with `Icon + Side + Front + Top` in one image, then stop for human approval of style, direction, and scale.
3. Generate `.vox` assets and side/front/top reference views from the approved sheet.
4. Run validators, especially `single_connected_component` and `floating_component_sizes`.
5. Review in `viewer/index.html`; the Reference pane shows the source sheet first, then generated `Icon / Side / Front / Top`.
6. Optionally apply a project adapter, such as LittleWorld Unity prefabs.

## Commands

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

The viewer is static. Open `viewer/index.html` directly, or run `node viewer/server.mjs` and open `http://127.0.0.1:5177/viewer/index.html` if a browser blocks local file access.

`generate-quick-trial` creates a second sample dataset under `examples/quick_trial` to exercise a fresh asset set without replacing the original design-sheet trial.
`generate-dog-trial` demonstrates the source-sheet flow with one approved image containing `Icon + Side + Front + Top`.
