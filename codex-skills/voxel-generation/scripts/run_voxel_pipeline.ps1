param(
  [Parameter(Mandatory=$true)]
  [ValidateSet(
    'generate-design-sheet',
    'check-design-sheet',
    'generate-quick-trial',
    'check-quick-trial',
    'generate-dog-trial',
    'check-dog-trial',
    'check-source-sheet',
    'build-viewer-data',
    'apply-littleworld'
  )]
  [string]$Command,

  [string]$PipelineRoot = (Get-Location).Path,
  [string]$Project = 'E:\AI Projects\LittleWorld',
  [string]$Image,
  [string]$Asset,
  [string]$Side,
  [string]$Front,
  [string]$Top,
  [string]$Tolerance = '4',
  [string]$OriginTolerance = '4',
  [string]$GridLineTolerance = '12',
  [string]$SideFrame,
  [string]$FrontFrame,
  [string]$TopFrame,
  [switch]$AllowColoredAnnotations,
  [string]$JsonOut
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
  } elseif ($Command -eq 'check-source-sheet') {
    foreach ($required in @('Image', 'Asset', 'Side', 'Front', 'Top')) {
      if (-not (Get-Variable -Name $required -ValueOnly)) {
        throw "check-source-sheet requires -$required"
      }
    }
    $argsList = @(
      'voxel_pipeline.py',
      $Command,
      '--image', $Image,
      '--asset', $Asset,
      '--side', $Side,
      '--front', $Front,
      '--top', $Top,
      '--tolerance', $Tolerance,
      '--origin-tolerance', $OriginTolerance,
      '--grid-line-tolerance', $GridLineTolerance
    )
    if ($SideFrame) { $argsList += @('--side-frame', $SideFrame) }
    if ($FrontFrame) { $argsList += @('--front-frame', $FrontFrame) }
    if ($TopFrame) { $argsList += @('--top-frame', $TopFrame) }
    if ($AllowColoredAnnotations) { $argsList += '--allow-colored-annotations' }
    if ($JsonOut) { $argsList += @('--json-out', $JsonOut) }
    python @argsList
  } else {
    python voxel_pipeline.py $Command
  }
} finally {
  Pop-Location
}
