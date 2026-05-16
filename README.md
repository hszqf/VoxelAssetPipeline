# VoxelAssetPipeline

Standalone voxel asset workflow extracted from LittleWorld.

## Workflow

1. Generate or provide a first-step reference image.
2. Stop for human approval of style, direction, and scale.
3. Generate `.vox` assets and side/front/top reference views.
4. Run validators, especially `single_connected_component` and `floating_component_sizes`.
5. Review in `viewer/index.html`.
6. Optionally apply a project adapter, such as LittleWorld Unity prefabs.

## Commands

```powershell
python voxel_pipeline.py generate-design-sheet
python voxel_pipeline.py check-design-sheet
python voxel_pipeline.py build-viewer-data
python voxel_pipeline.py apply-littleworld --project "E:\AI Projects\LittleWorld"
```

The viewer is static. Open `viewer/index.html` directly, or run `node viewer/server.mjs` and open `http://127.0.0.1:5177/viewer/index.html` if a browser blocks local file access.
