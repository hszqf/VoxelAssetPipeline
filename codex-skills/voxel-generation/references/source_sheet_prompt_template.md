# Voxel Orthographic Source Sheet Prompt Template

Use this after the front/back style reference has been approved. Fill every
placeholder from the user-confirmed generated asset dimensions and three-view
panel specification.

```text
Create one clean voxel game asset orthographic source sheet for exactly one asset.

This must be a production blueprint source sheet, not a polished render.

Use the approved front/back style reference as the visual source of truth for:
- colors
- front/back direction
- face/head/tail identity
- markings and distinctive features

Asset:
- name: {{asset_name}}
- subject: {{asset_description}}
- style: clean low-poly voxel icon design, readable small game asset, simple connected forms

Rendering style:
- Flat blocky voxel-pixel blueprint art.
- Use simple solid color rectangles aligned to the visible grid.
- No soft shadows, no cast shadows, no gradients, no glossy lighting.
- No 3D perspective, no isometric view, no presentation render.
- Avoid decorative anti-aliased edges; keep silhouettes crisp and measurable.

User confirmed specification:
- generated asset dimensions: {{asset_dimensions}}
- three-view panel grid: {{panel_width}} x {{panel_height}} cells per orthographic panel
- Side target full silhouette: {{side_length}} cells length x {{height}} cells height
- Front target full silhouette: {{front_width}} cells width x {{height}} cells height
- Top target full silhouette: {{side_length}} cells length x {{front_width}} cells depth
- tolerance: +/- {{tolerance}} cells
- The full silhouette includes all protrusions: muzzle, ears, horns, tail, hooves, handles, wings, markings, and accessories.
- Leave clear empty grid margin around the full silhouette when the requested dimensions are smaller than the panel. Do not enlarge the asset to fill the three-view panel.

Sheet layout, left to right:
1. registered Side {{panel_width}} x {{panel_height}} grid
2. registered Front {{panel_width}} x {{panel_height}} grid
3. registered Top {{panel_width}} x {{panel_height}} grid

Orthographic registration:
- Side view uses X length horizontally and Y height vertically.
- Front view uses Z width/depth horizontally and Y height vertically.
- Top view uses X length horizontally and Z width/depth vertically.
- Top view must place the asset's length horizontally on X, same front/head and back/tail direction as the Side view.
- Side length must match Top length.
- Front width must match Top depth.
- Side height must match Front height.
- Side and Front must share the same ground baseline.
- Body center, head/front extent, back/tail extent, legs, ears/horns, wings, handles, and major markings must line up across Side, Front, and Top.

Clean-grid requirements:
- Use a light neutral background.
- Side, Front, and Top must each have a visible {{panel_width}} x {{panel_height}} light gray grid and a plain bounding frame.
- Draw the grid lines on the top layer above the asset art in all three panels, so the grid remains visible across the silhouette.
- Each grid must genuinely read as {{panel_width}} cells by {{panel_height}} cells. Do not draw a vague decorative grid.
- Each panel must be a square blueprint panel. Keep the three grid panels separated and fully visible.
- Do not draw colored axes, colored dashed baselines, measurement arrows, brackets, or dimension numbers inside the grid panels.
- Do not draw blue/red/green guide labels inside the grid panels.
- Do not draw coordinate numbers, tick labels, legends, or scale text anywhere in or around the panels.
- Panel titles are allowed above panels only.
- The grid is a design guide only; the actual full silhouette must visibly fit the target dimensions.

Reject conditions:
- More than one asset appears.
- The image looks like a polished voxel render instead of a flat orthographic blueprint.
- Any orthographic panel is separately centered instead of registered to the same coordinate system.
- The Top view is rotated so length is vertical instead of horizontal.
- The visible full silhouette exceeds the target bounds by more than +/- {{tolerance}} cells.
- The orthographic views contradict the approved front/back style reference.
```

After generation, run the source-sheet checker before asking the user for
approval:

```powershell
python voxel_pipeline.py check-source-sheet `
  --image "<source-sheet.png>" `
  --asset "{{asset_name}}" `
  --side "{{side_length}}x{{height}}" `
  --front "{{front_width}}x{{height}}" `
  --top "{{side_length}}x{{front_width}}" `
  --tolerance "{{tolerance}}" `
  --json-out "<source-sheet-report.json>"
```

If the checker fails, report the failed checks first. Do not create
`VoxelModel`, `.vox`, manifests, or viewer data from the failed source sheet.
