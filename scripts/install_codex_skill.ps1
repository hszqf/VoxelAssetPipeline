param(
  [string]$SkillName = 'voxel-generation',
  [string]$CodexSkillsRoot
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot "codex-skills\$SkillName"

if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) {
  throw "Skill source not found: $source"
}

if (-not $CodexSkillsRoot) {
  $profileRoot = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
  $CodexSkillsRoot = Join-Path $profileRoot '.codex\skills'
}

$destination = Join-Path $CodexSkillsRoot $SkillName
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $source 'SKILL.md') -Destination $destination -Force

foreach ($folder in @('agents', 'references', 'scripts')) {
  $folderSource = Join-Path $source $folder
  if (Test-Path -LiteralPath $folderSource) {
    Copy-Item -LiteralPath $folderSource -Destination $destination -Recurse -Force
  }
}

Write-Host "Installed $SkillName to $destination"
Write-Host "Restart Codex or refresh the skill list before using the installed skill."
