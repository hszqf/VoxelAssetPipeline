# Voxel Reference Workflow

Default source reference format:

```text
Icon | Front 3/4 | Side | Front | Top
```

Use one raster image that contains the final icon-style view, a side-front three-quarter view, and the three orthographic views. This keeps the visual target and the structural constraints together, which reduces ambiguous features such as accidental raised blocks on an animal's back or confusing front/back orientation.

Workflow:

1. Generate or provide the combined source sheet.
2. Stop for approval before writing `.vox`.
3. Build the voxel model from the approved sheet.
4. Render generated review views: `Icon`, `Front 3/4`, `Side`, `Front`, and `Top`.
5. Run structural checks, especially `single_connected_component` and `floating_component_sizes`.
6. Rebuild `viewer/embedded-data.js`.
7. Review in `viewer/index.html`; the Reference pane should show `Source` first, followed by generated `Icon / Front 3/4 / Side / Front / Top`.

For animals and character assets:

- Treat top view as authoritative for back silhouette and markings.
- Add or inspect `Front 3/4` when the asset has a face, snout, chest, or other direction-specific front detail.
- Do not add a raised back patch unless it is visible in side and top views.
- Prefer flat, connected body volumes before adding decorative color variation.
