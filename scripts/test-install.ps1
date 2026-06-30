<#
.SYNOPSIS
    Run install.ps1 inside an isolated temporary USERPROFILE.
.DESCRIPTION
    This script validates installer behavior without touching the real Codex
    profile, marketplace, plugin cache, hooks, or automations.
#>

$ErrorActionPreference = "Stop"

$PluginRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$InstallScript = Join-Path $PluginRoot "install.ps1"
$TempProfile = Join-Path ([System.IO.Path]::GetTempPath()) ("cp-memory-install-test-" + [guid]::NewGuid().ToString("N"))

function Assert-PathExists {
    param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    if (-not (Test-Path $Path)) {
        throw "Expected path does not exist: $Path"
    }
}

function Assert-JsonPathValue {
    param(
        [Parameter(Mandatory=$true)]$Object,
        [Parameter(Mandatory=$true)][string]$Name
    )
    if (-not $Object.$Name) {
        throw "Expected JSON property is missing: $Name"
    }
}

try {
    New-Item -ItemType Directory -Force -Path (Join-Path $TempProfile ".codex") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $TempProfile ".agents\plugins") | Out-Null

    $configPath = Join-Path $TempProfile ".codex\config.toml"
    [System.IO.File]::WriteAllText($configPath, "model = `"gpt-5.5`"`n", [System.Text.UTF8Encoding]::new($false))

    $marketplacePath = Join-Path $TempProfile ".agents\plugins\marketplace.json"
    $marketplace = @{
        name = "personal"
        interface = @{ displayName = "Personal" }
        plugins = @()
    } | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($marketplacePath, $marketplace, [System.Text.UTF8Encoding]::new($false))

    $previousUserProfile = $env:USERPROFILE
    $env:USERPROFILE = $TempProfile
    try {
        & powershell -ExecutionPolicy Bypass -File $InstallScript | Out-Host
    } finally {
        $env:USERPROFILE = $previousUserProfile
    }

    $installedRoot = Join-Path $TempProfile "plugins\cp-memory"
    $cacheRoot = Join-Path $TempProfile ".codex\plugins\cache\personal\cp-memory\1.0.21"
    $automationFile = Join-Path $TempProfile ".codex\automations\cp-memory-weekly-maintenance\automation.toml"

    Assert-PathExists (Join-Path $installedRoot ".codex-plugin\plugin.json")
    Assert-PathExists (Join-Path $installedRoot "hooks\claude-codex-hooks.json")
    Assert-PathExists (Join-Path $cacheRoot ".codex-plugin\plugin.json")
    Assert-PathExists (Join-Path $cacheRoot ".mcp.json")
    Assert-PathExists $automationFile

    $installedManifest = Get-Content (Join-Path $installedRoot ".codex-plugin\plugin.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    Assert-JsonPathValue -Object $installedManifest -Name "hooks"
    Assert-JsonPathValue -Object $installedManifest -Name "mcpServers"

    $updatedMarketplace = Get-Content $marketplacePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not (@($updatedMarketplace.plugins) | Where-Object { $_.name -eq "cp-memory" })) {
        throw "cp-memory was not registered in the isolated personal marketplace."
    }

    $globalHooksFile = Join-Path $TempProfile ".codex\hooks.json"
    if (Test-Path $globalHooksFile) {
        $globalHooks = Get-Content $globalHooksFile -Raw -Encoding UTF8
        if ($globalHooks -match "cp_memory_common.py|session_start.py|user_prompt_submit.py|pre_compact.py|stop.py") {
            throw "Installer wrote legacy CP Memory hook scripts into isolated global hooks.json."
        }
    }

    Write-Host "Isolated install test passed: $TempProfile" -ForegroundColor Green
} finally {
    if (Test-Path $TempProfile) {
        Remove-Item -LiteralPath $TempProfile -Recurse -Force
    }
}
