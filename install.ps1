<#
.SYNOPSIS
    Install CP Memory plugin for Codex
.DESCRIPTION
    Copies plugin files, registers the plugin in the personal marketplace, enables it in config,
    refreshes the cache, and migrates any legacy global hook wiring to plugin-native hooks.
#>

$ErrorActionPreference = "Stop"
$PluginName = "cp-memory"
$PluginVersion = "1.0.21"
$PluginSource = "$PSScriptRoot"
$CodexHome = "$env:USERPROFILE\.codex"
$AgentsHome = "$env:USERPROFILE\.agents"
$PluginTarget = "$env:USERPROFILE\plugins\$PluginName"
$MarketplaceFile = "$AgentsHome\plugins\marketplace.json"
$ConfigFile = "$CodexHome\config.toml"
$CacheRoot = "$CodexHome\plugins\cache\personal\$PluginName"
$CacheDir = "$CacheRoot\$PluginVersion"
$LegacyHooksDir = "$CodexHome\hooks"
$LegacyHooksConfigFile = "$CodexHome\hooks.json"
$AutomationsRoot = "$CodexHome\automations"
$WeeklyAutomationId = "cp-memory-weekly-maintenance"
$WeeklyAutomationDir = "$AutomationsRoot\$WeeklyAutomationId"
$WeeklyAutomationFile = "$WeeklyAutomationDir\automation.toml"
$WeeklyAutomationPromptFile = "$PluginSource\resources\weekly-maintenance-prompt.zh-CN.txt"
$WeeklyAutomationTemplateFile = "$PluginSource\resources\weekly-maintenance.automation.toml.tpl"

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Content
    )
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function ConvertTo-TomlBasicString {
    param(
        [AllowNull()][string]$Value
    )
    if ($null -eq $Value) {
        $Value = ""
    }
    $escaped = $Value.Replace('\', '\\').Replace('"', '\"').Replace("`t", '\t').Replace("`r", '\r').Replace("`n", '\n')
    return '"' + $escaped + '"'
}

function Test-TomlFile {
    param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    python -c "import pathlib,tomllib; tomllib.loads(pathlib.Path(r'$Path').read_text(encoding='utf-8'))" | Out-Null
}

function Write-TomlValidatedFile {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Content
    )
    $backup = ""
    if (Test-Path $Path) {
        $backup = "$Path.bak"
        Copy-Item -LiteralPath $Path -Destination $backup -Force
    }
    try {
        Write-Utf8NoBom -Path $Path -Content $Content
        Test-TomlFile -Path $Path
        if ($backup -and (Test-Path $backup)) {
            Remove-Item -LiteralPath $backup -Force
        }
    } catch {
        if ($backup -and (Test-Path $backup)) {
            Move-Item -LiteralPath $backup -Destination $Path -Force
        } elseif (Test-Path $Path) {
            Remove-Item -LiteralPath $Path -Force
        }
        throw
    }
}

function Test-IsLegacyCpMemoryHookCommand {
    param(
        [AllowNull()][string]$Command
    )
    if ([string]::IsNullOrWhiteSpace($Command)) {
        return $false
    }
    $normalized = $Command.Replace('/', '\').ToLowerInvariant()
    if ($normalized -notlike "*\.codex\hooks\*") {
        return $false
    }
    foreach ($scriptName in @("session_start.py", "user_prompt_submit.py", "pre_compact.py", "stop.py")) {
        if ($normalized -like "*$scriptName*") {
            return $true
        }
    }
    return $false
}

function Remove-LegacyCpMemoryHookRegistration {
    param(
        [Parameter(Mandatory=$true)][string]$HooksConfigPath
    )
    if (-not (Test-Path $HooksConfigPath)) {
        return
    }
    $raw = Get-Content $HooksConfigPath -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return
    }
    $config = ConvertFrom-Json $raw
    if (-not $config.hooks) {
        return
    }

    $changed = $false
    $filteredHooks = [ordered]@{}
    foreach ($eventProperty in $config.hooks.PSObject.Properties) {
        $eventName = $eventProperty.Name
        $eventEntries = @($eventProperty.Value)
        $keptEntries = @()
        foreach ($eventEntry in $eventEntries) {
            $entry = [ordered]@{}
            foreach ($property in $eventEntry.PSObject.Properties) {
                if ($property.Name -eq "hooks") {
                    continue
                }
                $entry[$property.Name] = $property.Value
            }
            $remainingHooks = @()
            foreach ($hook in @($eventEntry.hooks)) {
                if (Test-IsLegacyCpMemoryHookCommand $hook.command) {
                    $changed = $true
                    continue
                }
                $remainingHooks += ,$hook
            }
            if ($remainingHooks.Count -gt 0) {
                $entry["hooks"] = $remainingHooks
                $keptEntries += ,$entry
            } else {
                $changed = $true
            }
        }
        if ($keptEntries.Count -gt 0) {
            $filteredHooks[$eventName] = $keptEntries
        }
    }

    if (-not $changed) {
        return
    }

    $result = [ordered]@{ hooks = $filteredHooks }
    Write-Utf8NoBom -Path $HooksConfigPath -Content ($result | ConvertTo-Json -Depth 20)
}

function Remove-LegacyCpMemoryHookFiles {
    param(
        [Parameter(Mandatory=$true)][string]$HooksDirPath
    )
    foreach ($scriptName in @("cp_memory_common.py", "session_start.py", "user_prompt_submit.py", "pre_compact.py", "stop.py")) {
        $path = Join-Path $HooksDirPath $scriptName
        if (Test-Path $path) {
            Remove-Item -LiteralPath $path -Force
        }
    }
}

Write-Host "=== Installing $PluginName v$PluginVersion ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/8] Copying plugin source..." -NoNewline
$sourceFull = [System.IO.Path]::GetFullPath($PluginSource).TrimEnd('\')
$targetFull = [System.IO.Path]::GetFullPath($PluginTarget).TrimEnd('\')
if ($sourceFull -ne $targetFull) {
    if (Test-Path $PluginTarget) { Remove-Item -Recurse -Force $PluginTarget }
    New-Item -ItemType Directory -Force -Path $PluginTarget | Out-Null
    Get-ChildItem -Path $PluginSource -Exclude "install.ps1" | Copy-Item -Destination $PluginTarget -Recurse -Force
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[2/8] Registering in marketplace..." -NoNewline
if (-not (Test-Path "$AgentsHome\plugins")) { New-Item -ItemType Directory -Force -Path "$AgentsHome\plugins" | Out-Null }
if (Test-Path $MarketplaceFile) {
    $mp = Get-Content $MarketplaceFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $mp.plugins = @($mp.plugins | Where-Object { $_.name -ne $PluginName })
    $entry = @{
        name = $PluginName
        source = @{ source = "local"; path = "./plugins/$PluginName" }
        policy = @{ installation = "AVAILABLE"; authentication = "ON_INSTALL" }
        category = "Productivity"
    }
    $mp.plugins += $entry
    Write-Utf8NoBom -Path $MarketplaceFile -Content ($mp | ConvertTo-Json -Depth 10)
} else {
    $mp = @{
        name = "personal"
        interface = @{ displayName = "Personal" }
        plugins = @(@{
            name = $PluginName
            source = @{ source = "local"; path = "./plugins/$PluginName" }
            policy = @{ installation = "AVAILABLE"; authentication = "ON_INSTALL" }
            category = "Productivity"
        })
    }
    Write-Utf8NoBom -Path $MarketplaceFile -Content ($mp | ConvertTo-Json -Depth 10)
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[3/8] Enabling plugin in config.toml..." -NoNewline
if (Test-Path $ConfigFile) {
    $cfg = Get-Content $ConfigFile -Raw -Encoding UTF8
    $entry = "[plugins.`"$PluginName@personal`"]`nenabled = true"
    if ($cfg -notmatch "`"$PluginName@personal`"") {
        $cfg = $cfg.TrimEnd() + "`n`n$entry`n"
        Write-TomlValidatedFile -Path $ConfigFile -Content $cfg
    }
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[4/8] Refreshing cache..." -NoNewline
if (Test-Path $CacheRoot) { Remove-Item -Recurse -Force $CacheRoot }
New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null
Get-ChildItem -Path $PluginTarget | Copy-Item -Destination $CacheDir -Recurse -Force
$sourcePluginJson = "$PluginTarget\.codex-plugin\plugin.json"
$cachePluginJson = "$CacheDir\.codex-plugin\plugin.json"
foreach ($path in @($sourcePluginJson, $cachePluginJson)) {
    if (Test-Path $path) {
        $pluginJson = Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json
        $pluginJson.version = $PluginVersion
        Write-Utf8NoBom -Path $path -Content ($pluginJson | ConvertTo-Json -Depth 10)
    }
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[5/8] Cleaning legacy global hook wiring..." -NoNewline
New-Item -ItemType Directory -Force -Path $LegacyHooksDir | Out-Null
Remove-LegacyCpMemoryHookFiles -HooksDirPath $LegacyHooksDir
Remove-LegacyCpMemoryHookRegistration -HooksConfigPath $LegacyHooksConfigFile
Write-Host " OK" -ForegroundColor Green

Write-Host "[6/8] Provisioning weekly maintenance automation..." -NoNewline
New-Item -ItemType Directory -Force -Path $WeeklyAutomationDir | Out-Null
$createdAt = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
if (Test-Path $WeeklyAutomationFile) {
    $existing = Get-Content $WeeklyAutomationFile -Raw -Encoding UTF8
    $match = [regex]::Match($existing, '(?m)^created_at\s*=\s*(\d+)\s*$')
    if ($match.Success) {
        $createdAt = $match.Groups[1].Value
    }
}
$updatedAt = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$weeklyPrompt = Get-Content $WeeklyAutomationPromptFile -Raw -Encoding UTF8
$weeklyPromptSingleLine = (($weeklyPrompt -split "\r?\n") -join " ").Trim()
$weeklyTemplate = Get-Content $WeeklyAutomationTemplateFile -Raw -Encoding UTF8
$weeklyAutomationToml = $weeklyTemplate
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_ID}}", $WeeklyAutomationId)
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_NAME}}", "CP Memory Weekly Maintenance")
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_PROMPT}}", (ConvertTo-TomlBasicString $weeklyPromptSingleLine))
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_STATUS}}", "ACTIVE")
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_RRULE}}", "FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0")
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_MODEL}}", "gpt-5.5")
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_REASONING_EFFORT}}", "medium")
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_EXECUTION_ENVIRONMENT}}", "local")
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_CWD}}", (ConvertTo-TomlBasicString $PluginTarget))
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_CREATED_AT}}", [string]$createdAt)
$weeklyAutomationToml = $weeklyAutomationToml.Replace("{{AUTOMATION_UPDATED_AT}}", [string]$updatedAt)
Write-TomlValidatedFile -Path $WeeklyAutomationFile -Content $weeklyAutomationToml
$duplicateAutomationDirs = Get-ChildItem -Path $AutomationsRoot -Directory -ErrorAction SilentlyContinue | Where-Object {
    $_.FullName -ne $WeeklyAutomationDir -and $_.Name -like "$WeeklyAutomationId-*"
}
foreach ($dir in $duplicateAutomationDirs) {
    Remove-Item -Recurse -Force $dir.FullName
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[7/8] Validating config.toml..." -NoNewline
if (Test-Path $ConfigFile) {
    Test-TomlFile -Path $ConfigFile
}
Write-Host " OK" -ForegroundColor Green

Write-Host "[8/8] Validating Python entry points..." -NoNewline
python -m py_compile `
    "$PluginTarget\scripts\cp_memory_store.py" `
    "$PluginTarget\scripts\memory-mcp-server.py" `
    "$PluginTarget\hooks\cp_memory_common.py" `
    "$PluginTarget\hooks\session_start.py" `
    "$PluginTarget\hooks\pre_compact.py" `
    "$PluginTarget\hooks\stop.py" `
    "$PluginTarget\hooks\user_prompt_submit.py" | Out-Null
Write-Host " OK" -ForegroundColor Green

Write-Host ""
Write-Host "=== Installation complete! ===" -ForegroundColor Cyan
Write-Host "Restart Codex so the refreshed hooks, skills, and plugin cache all take effect." -ForegroundColor Yellow
