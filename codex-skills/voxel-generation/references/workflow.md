# Voxel Asset Pipeline Workflow

Core invariant: first source-sheet approval happens before `.vox` generation.

Default source reference format:

```text
Icon | Front 3/4 | Side | Front | Top
```

Use one raster image that contains the final icon-style view, a side-front three-quarter view, and the three orthographic views. This keeps the visual target and the structural constraints together, reducing ambiguous features such as accidental raised blocks on an animal's back or confusing front/back orientation.

Pipeline stages:

1. Source sheet: generated or user-provided, used to settle visual style, orientation, scale, and silhouette.
2. Approval stop: do not write `.vox` until the user approves the source sheet.
3. Voxel construction: convert into a structured `VoxelModel` array and write MagicaVoxel `.vox`.
4. Review renders: source sheet plus generated icon, front three-quarter, and side/front/top views inside a 64-cell guide. Add the asset's model/manifest name in the upper-left corner of every generated source/review row.
5. Validation: size, one-cell fit, domain-specific checks, `single_connected_component`, and `floating_component_sizes`.
6. Viewer: rebuild `viewer/embedded-data.js` so `viewer/index.html` works from `file://`; the Reference pane should show `Source` first, then generated `Icon / Front 3/4 / Side / Front / Top`.
7. Adapter: apply only after user approval.

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

Animal and character assets:

- Treat top view as authoritative for back silhouette and markings.
- Add or inspect `Front 3/4` when the asset has a face, snout, chest, or other direction-specific front detail.
- Do not add a raised back patch unless it is visible in side and top views.
- Prefer flat, connected body volumes before adding decorative color variation.
