param(
  [Parameter(Mandatory=$true)]
  [ValidateSet(
    'generate-design-sheet',
    'check-design-sheet',
    'generate-quick-trial',
    'check-quick-trial',
    'generate-dog-trial',
    'check-dog-trial',
    'build-viewer-data',
    'apply-littleworld'
  )]
  [string]$Command,

  [string]$PipelineRoot = (Get-Location).Path,
  [string]$Project = 'E:\AI Projects\LittleWorld'
)

$pipelineRootResolved = Resolve-Path -LiteralPath $PipelineRoot -ErrorAction Stop
$pipelineScript = Join-Path $pipelineRootResolved 'voxel_pipeline.py'

if (-not (Test-Path -LiteralPath $pipelineScript)) {
  throw "PipelineRoot must point to a VoxelAssetPipeline clone containing voxel_pipeline.py: $PipelineRoot"
}

Push-Location -LiteralPath $pipelineRootResolved
try {
  if ($Command -eq 'apply-littleworld') {
    python voxel_pipeline.py $Command --project $Project
  } else {
    python voxel_pipeline.py $Command
  }
} finally {
  Pop-Location
}
