# Voxel Style Reference Prompt Template

Use this first. This image decides style and direction only; it is not used for
cell measurements.

```text
Create one clean voxel game asset style reference for exactly one asset.

Asset:
- name: {{asset_name}}
- subject: {{asset_description}}
- style: clean low-poly voxel icon design, readable small game asset, simple connected forms

Views:
1. Front 3/4 design
2. Back 3/4 design

Requirements:
- Show the same asset in both views with matching colors, proportions, and distinctive features.
- Make the front direction, face, head, tail/back, and important markings unambiguous.
- Keep the design simple enough to build as voxels.
- Do not include Side/Front/Top orthographic grids in this image.
- Do not include 64-cell measurement grids, colored axes, arrows, or dimension labels.
- Do not generate more than one asset.
```

Approval gate:

- Use this image to approve style, front/back identity, colors, and overall silhouette.
- Do not measure occupied 64-cell bounds from this image.
- Do not create `.vox` from this image alone.
