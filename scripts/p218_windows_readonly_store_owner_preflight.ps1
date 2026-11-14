# P218: read-only Windows platform observation; never creates a service or accesses secrets.
# This is a diagnostic for external G0/R3 review, NOT an admission or security gate.
# Supported PowerShell: 5.1+ on Windows. Output: minimal, non-secret JSON only.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'P218 requires native Windows: no simulated pass'
}
$osInfo = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
if ($null -eq $osInfo) { throw 'P218 Windows OS identity unproven' }
$service = @(Get-CimInstance -ClassName Win32_Service -Filter "Name='NayeonByokCustody'" -ErrorAction Stop)
$ciTool = Get-Command CiTool.exe -ErrorAction SilentlyContinue
$state = 'UNPROVEN'
$total = $null
$enforced = $null
$notEnforced = $null
$ciExit = $null
if ($null -ne $ciTool) {
    # This is the read-only listing form; NEVER update, remove, refresh or install.
    $raw = @(CiTool.exe --list-policies --json 2>&1)
    $ciExit = $LASTEXITCODE
    if ($ciExit -eq 0) {
        try {
            $response = ($raw -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop
            if ($null -ne $response -and $null -ne $response.Policies) {
                $policies = @($response.Policies)
                $withEnforcement = @($policies | Where-Object {
                    $_.PSObject.Properties.Name -contains 'IsEnforced' -and
                    $null -ne $_.IsEnforced
                })
                if ($withEnforcement.Count -eq $policies.Count) {
                    $total = $policies.Count
                    $enforced = @($policies | Where-Object { $_.IsEnforced -eq $true }).Count
                    $notEnforced = @($policies | Where-Object { $_.IsEnforced -eq $false }).Count
                    $state = 'OBSERVED'
                }
            }
        } catch {
            $state = 'UNPROVEN'
        }
    }
}
$report = [ordered]@{
    schema = 'P218-WindowsReadOnlyObservation-v1'
    observation_only = $true
    runner_scope = $(if ($env:GITHUB_ACTIONS -eq 'true') { 'GITHUB_HOSTED_RUNNER' } else { 'CURRENT_WINDOWS_DEVICE' })
    os_caption = [string]$osInfo.Caption
    os_version = [string]$osInfo.Version
    os_build = [string]$osInfo.BuildNumber
    service_named_NayeonByokCustody_present = ($service.Count -gt 0)
    advapi32_dll_present = [bool](Test-Path -LiteralPath "$env:SystemRoot\System32\advapi32.dll")
    ci_tool_available = ($null -ne $ciTool)
    ci_readonly_exit = $ciExit
    ci_policy_observation = $state
    ci_policy_total = $total
    ci_policy_is_enforced_true = $enforced
    ci_policy_is_enforced_false = $notEnforced
    service_account_profile_verified = $false
    service_user_dpapi_verified = $false
    loaded_signed_service_image_verified = $false
    independent_G0_R3_decision_received = $false
    legacy_P132_effect_isolated = $false
    credential_effect_executed = $false
    real_key_authorised = $false
    production_release_authorised = $false
    status = 'G0_R3_HOLD'
}
# No raw policy GUIDs, credentials, user SIDs, certificates, paths or key material.
$report | ConvertTo-Json -Compress -Depth 3
