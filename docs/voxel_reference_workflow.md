# Voxel Reference Workflow

The first approved reference must be a design image, not a voxel render produced by this pipeline.

Default source reference format:

```text
Icon | Front 3/4 | Side | Front | Top
```

Use one raster image that contains the final icon-style view, a side-front three-quarter view, and the three orthographic views. This keeps the visual target and the structural constraints together, which reduces ambiguous features such as accidental raised blocks on an animal's back or confusing front/back orientation.

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
2. Stop for approval before creating voxel geometry or writing `.vox`.
3. Build the voxel model from the approved sheet.
4. Render generated review views: `Icon`, `Front 3/4`, `Side`, `Front`, and `Top`.
5. Run structural checks, especially `single_connected_component` and `floating_component_sizes`.
6. Rebuild `viewer/embedded-data.js`.
7. Review in `viewer/index.html`; the Reference pane should show `Source` first, followed by generated `Icon / Front 3/4 / Side / Front / Top`.

Viewer dataset registration:

- Put each review batch under `examples/<batch_name>/manifest.json`.
- Run `python voxel_pipeline.py build-viewer-data`.
- `viewer/build-embedded-data.mjs` scans `examples/*/manifest.json` and writes `window.VOX_VIEWER_EMBEDDED.datasets`.
- `viewer/app.js` builds the Set dropdown from the embedded dataset metadata.
- Do not add batch names manually to `viewer/app.js`.
- Add optional `examples/<batch_name>/dataset.json` only when the displayed name, id, cell resolution, or order needs to be overridden.

If a script-rendered voxel draft was used as the first source image, discard it and restart from the design-source step. Do not patch the model forward; errors such as duplicated limbs usually come from skipping the design-source gate.

For animals and character assets:

- Treat top view as authoritative for back silhouette and markings.
- Add or inspect `Front 3/4` when the asset has a face, snout, chest, or other direction-specific front detail.
- Do not add a raised back patch unless it is visible in side and top views.
- Prefer flat, connected body volumes before adding decorative color variation.
