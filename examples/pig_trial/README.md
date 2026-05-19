# Voxel Pig Source Cleanup Notes

Final approved source cleanup:

- Input AI/user sheet: `voxel_pig_source_32_attempt2.png`
- Approved clean source: `voxel_pig_source_32_attempt2_linecut_mode.png`
- Reproducible CLI output: `voxel_pig_source_32_attempt2_linecut_mode_cli.png`
- Gridline overlay: `voxel_pig_source_32_attempt2_gridline_overlay_cli.png`
- Cleaner report: `source_32_attempt2_linecut_mode_cli_cells.json`
- Checker report: `source_32_attempt2_linecut_mode_cli_report.json`

The successful cleanup does not redraw semantic features. It detects the original
AI-drawn grid lines, cuts cells by those source line positions, centers source
cells into a clean `32 x 32` grid, and assigns each output cell the dominant raw
RGB bucket among non-background pixels in the original source cell.

Reproduce the cleanup from the repository root:

```powershell
python voxel_pipeline.py clean-source-sheet `
  --image "examples/pig_trial/voxel_pig_source_32_attempt2.png" `
  --asset voxel_pig `
  --grid-size 32 `
  --bucket-size 8 `
  --out "examples/pig_trial/voxel_pig_source_32_attempt2_linecut_mode_cli.png" `
  --overlay-out "examples/pig_trial/voxel_pig_source_32_attempt2_gridline_overlay_cli.png" `
  --json-out "examples/pig_trial/source_32_attempt2_linecut_mode_cli_cells.json"
```

Then verify the cleaned source:

```powershell
python voxel_pipeline.py check-source-sheet `
  --image "examples/pig_trial/voxel_pig_source_32_attempt2_linecut_mode_cli.png" `
  --asset voxel_pig `
  --side 20x15 `
  --front 9x15 `
  --top 19x9 `
  --grid-size 32 `
  --tolerance 1 `
  --origin-tolerance 2 `
  --grid-line-tolerance 1 `
  --allow-colored-annotations `
  --json-out "examples/pig_trial/source_32_attempt2_linecut_mode_cli_report.json"
```

Expected checker result:

- Side observed about `20 x 15`
- Front observed about `9 x 15`
- Top observed about `19 x 9`
- Side length matches Top length within tolerance
- Front width matches Top depth within tolerance
- Side height matches Front height within tolerance
- Ground baseline matches
- `pass: true`

Generate the voxel asset after source approval:

```powershell
python voxel_pipeline.py generate-pig-trial
```

The generation workflow reads `voxel_pig_source_32_attempt2_linecut_mode_cli.png`,
builds `voxel_pig.vox` from the approved Side/Front/Top masks using a visual-hull
intersection, applies visible surface colors sampled from the source cells, writes
review renders, and runs `check-pig-trial`.

Expected generated asset:

- Output `.vox`: `voxel_pig.vox`
- Size: `20 x 15 x 9`
- Cell resolution: `32`
- Structural checks: `single_connected_component` and no floating components
- Viewer dataset: `pig-trial`
