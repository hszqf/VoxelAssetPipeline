# Voxel Orthographic Source Sheet Prompt Template

Use this after the front/back style reference has been approved. Fill every
placeholder from the confirmed scale contract.

```text
Create one clean voxel game asset orthographic source sheet for exactly one asset.

Use the approved front/back style reference as the visual source of truth for:
- colors
- front/back direction
- face/head/tail identity
- markings and distinctive features

Asset:
- name: {{asset_name}}
- subject: {{asset_description}}
- style: clean low-poly voxel icon design, readable small game asset, simple connected forms

Scale contract:
- game_cells: {{game_cells}}
- one cell resolution: 64 x 64 x 64
- Side target full silhouette: {{side_length}} cells length x {{height}} cells height
- Front target full silhouette: {{front_width}} cells width x {{height}} cells height
- Top target full silhouette: {{side_length}} cells length x {{front_width}} cells depth
- tolerance: +/- {{tolerance}} cells
- The full silhouette includes all protrusions: muzzle, ears, horns, tail, hooves, handles, wings, markings, and accessories.
- Leave clear empty grid margin around the full silhouette. Do not enlarge the asset to fill the 64-cell frame.

Sheet layout, left to right:
1. registered Side 64-grid
2. registered Front 64-grid
3. registered Top 64-grid

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
- Side, Front, and Top must each have a visible 64 x 64 light gray grid and a plain bounding frame.
- Each grid must genuinely read as 64 cells by 64 cells. Do not draw a vague decorative grid.
- Do not draw colored axes, colored dashed baselines, measurement arrows, brackets, or dimension numbers inside the grid panels.
- Do not draw blue/red/green guide labels inside the grid panels.
- Panel titles are allowed above panels only.
- The grid is a design guide only; the actual full silhouette must visibly fit the target dimensions.

Reject conditions:
- More than one asset appears.
- Any orthographic panel is separately centered instead of registered to the same 64-cell coordinate system.
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
