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
    'clean-source-sheet',
    'build-viewer-data',
    'apply-littleworld'
  )]
  [string]$Command,

  [string]$PipelineRoot = (Get-Location).Path,
  [string]$Python,
  [string]$Project = 'E:\AI Projects\LittleWorld',
  [string]$Image,
  [string]$Asset,
  [string]$Side,
  [string]$Front,
  [string]$Top,
  [string]$Tolerance = '4',
  [string]$OriginTolerance = '4',
  [string]$GridLineTolerance = '12',
  [string]$GridSize,
  [string]$CellPx,
  [string]$BucketSize,
  [string]$SamplePadding,
  [string]$ObjectThreshold,
  [string]$Out,
  [string]$OverlayOut,
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

if (-not $Python) {
  $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (Test-Path -LiteralPath $bundledPython) {
    $Python = $bundledPython
  } else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
      $Python = $pythonCommand.Source
    } else {
      throw "Python was not found. Pass -Python <path-to-python.exe> or install python on PATH."
    }
  }
}

Push-Location -LiteralPath $pipelineRootResolved
try {
  if ($Command -eq 'apply-littleworld') {
    & $Python voxel_pipeline.py $Command --project $Project
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
    if ($GridSize) { $argsList += @('--grid-size', $GridSize) }
    if ($SideFrame) { $argsList += @('--side-frame', $SideFrame) }
    if ($FrontFrame) { $argsList += @('--front-frame', $FrontFrame) }
    if ($TopFrame) { $argsList += @('--top-frame', $TopFrame) }
    if ($AllowColoredAnnotations) { $argsList += '--allow-colored-annotations' }
    if ($JsonOut) { $argsList += @('--json-out', $JsonOut) }
    & $Python @argsList
  } elseif ($Command -eq 'clean-source-sheet') {
    foreach ($required in @('Image', 'Asset', 'Out')) {
      if (-not (Get-Variable -Name $required -ValueOnly)) {
        throw "clean-source-sheet requires -$required"
      }
    }
    $argsList = @(
      'voxel_pipeline.py',
      $Command,
      '--image', $Image,
      '--asset', $Asset,
      '--out', $Out
    )
    if ($GridSize) { $argsList += @('--grid-size', $GridSize) }
    if ($CellPx) { $argsList += @('--cell-px', $CellPx) }
    if ($BucketSize) { $argsList += @('--bucket-size', $BucketSize) }
    if ($SamplePadding) { $argsList += @('--sample-padding', $SamplePadding) }
    if ($ObjectThreshold) { $argsList += @('--object-threshold', $ObjectThreshold) }
    if ($SideFrame) { $argsList += @('--side-frame', $SideFrame) }
    if ($FrontFrame) { $argsList += @('--front-frame', $FrontFrame) }
    if ($TopFrame) { $argsList += @('--top-frame', $TopFrame) }
    if ($OverlayOut) { $argsList += @('--overlay-out', $OverlayOut) }
    if ($JsonOut) { $argsList += @('--json-out', $JsonOut) }
    & $Python @argsList
  } else {
    & $Python voxel_pipeline.py $Command
  }
} finally {
  Pop-Location
}
