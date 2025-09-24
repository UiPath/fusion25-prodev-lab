# Prerequisites Checker for Company Agent with UiPath (Windows)
# This script checks if all required software is installed and properly configured
# Excludes UiPath-specific prerequisites

$script:totalChecks = 0
$script:passedChecks = 0
$script:warnings = @()
$script:errors = @()

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )

    switch ($Type) {
        "Success" { Write-Host $Message -ForegroundColor Green }
        "Error" { Write-Host $Message -ForegroundColor Red }
        "Warning" { Write-Host $Message -ForegroundColor Yellow }
        "Info" { Write-Host $Message -ForegroundColor Cyan }
        "Header" {
            Write-Host ""
            Write-Host ("=" * 60) -ForegroundColor Blue
            Write-Host $Message -ForegroundColor Blue
            Write-Host ("=" * 60) -ForegroundColor Blue
        }
        default { Write-Host $Message }
    }
}

function Test-Command {
    param(
        [string]$Command,
        [string]$DisplayName,
        [string]$MinVersion = $null,
        [string]$VersionCommand = "--version",
        [switch]$Optional = $false
    )

    $script:totalChecks++
    Write-Host -NoNewline "Checking $DisplayName... "

    try {
        $result = Get-Command $Command -ErrorAction Stop

        if ($MinVersion) {
            $versionOutput = & $Command $VersionCommand 2>&1 | Out-String

            # Extract version number using regex
            if ($versionOutput -match '(\d+\.?\d*\.?\d*)') {
                $installedVersion = $matches[1]
                $installedParts = $installedVersion.Split('.')
                $requiredParts = $MinVersion.Split('.')

                $versionOk = $true
                for ($i = 0; $i -lt [Math]::Min($installedParts.Length, $requiredParts.Length); $i++) {
                    if ([int]$installedParts[$i] -lt [int]$requiredParts[$i]) {
                        $versionOk = $false
                        break
                    } elseif ([int]$installedParts[$i] -gt [int]$requiredParts[$i]) {
                        break
                    }
                }

                if ($versionOk) {
                    Write-ColorOutput "[OK] Found version $installedVersion" -Type "Success"
                    $script:passedChecks++
                } else {
                    $message = "[X] Version $installedVersion found, but $MinVersion or higher required"
                    if ($Optional) {
                        Write-ColorOutput $message -Type "Warning"
                        $script:warnings += "${DisplayName}: ${message}"
                    } else {
                        Write-ColorOutput $message -Type "Error"
                        $script:errors += "${DisplayName}: ${message}"
                    }
                }
            } else {
                Write-ColorOutput "[OK] Found (version unknown)" -Type "Success"
                $script:passedChecks++
            }
        } else {
            Write-ColorOutput "[OK] Found" -Type "Success"
            $script:passedChecks++
        }
    } catch {
        $message = "[X] Not found"
        if ($Optional) {
            Write-ColorOutput "$message (Optional)" -Type "Warning"
            $script:warnings += "${DisplayName}: Not installed (optional)"
        } else {
            Write-ColorOutput $message -Type "Error"
            $script:errors += "${DisplayName}: Not installed"
        }
    }
}

function Test-WindowsVersion {
    $script:totalChecks++
    Write-Host -NoNewline "Checking Windows version... "

    $os = Get-WmiObject -Class Win32_OperatingSystem
    $version = [System.Version]$os.Version

    # Windows 10 version 1903 is 10.0.18362
    # Windows 11 is 10.0.22000 or higher
    if ($version.Major -eq 10 -and $version.Build -ge 18362) {
        $osName = if ($version.Build -ge 22000) { "Windows 11" } else { "Windows 10" }
        Write-ColorOutput "[OK] $osName (Build $($version.Build))" -Type "Success"
        $script:passedChecks++
    } else {
        Write-ColorOutput "[X] Windows version too old (Build $($version.Build))" -Type "Error"
        $script:errors += "Windows - Version too old. Requires Windows 10 v1903 or later"
    }
}

# Main execution
Clear-Host
Write-ColorOutput "Prerequisites Checker for Company Agent with UiPath" -Type "Header"
Write-ColorOutput "Checking Windows prerequisites..." -Type "Info"
Write-Host ""

Write-ColorOutput "CHECKING PREREQUISITES" -Type "Info"
Write-Host ("-" * 40)

Test-WindowsVersion
Test-Command -Command "uv" -DisplayName "UV Package Manager" -VersionCommand "--version"
Test-Command -Command "git" -DisplayName "Git" -VersionCommand "--version"
Test-Command -Command "node" -DisplayName "Node.js" -MinVersion "14.0" -VersionCommand "--version"
Test-Command -Command "npm" -DisplayName "npm" -VersionCommand "--version"
Test-Command -Command "jupyter" -DisplayName "Jupyter" -VersionCommand "--version"
Test-Command -Command "cursor" -DisplayName "Cursor" -VersionCommand "--version"

# Summary
Write-Host ""
Write-ColorOutput "SUMMARY" -Type "Header"
Write-Host "Checks passed: $script:passedChecks / $script:totalChecks"

if ($script:errors.Count -gt 0) {
    Write-Host ""
    Write-ColorOutput "ERRORS (Must be fixed):" -Type "Error"
    foreach ($err in $script:errors) {
        Write-Host "  • $err" -ForegroundColor Red
    }
}

if ($script:warnings.Count -gt 0) {
    Write-Host ""
    Write-ColorOutput "WARNINGS (Recommended to fix):" -Type "Warning"
    foreach ($warning in $script:warnings) {
        Write-Host "  • $warning" -ForegroundColor Yellow
    }
}

# Installation commands
if ($script:errors.Count -gt 0) {
    Write-Host ""
    Write-ColorOutput "INSTALLATION COMMANDS" -Type "Info"
    Write-Host ("-" * 40)

    if ($script:errors -match "UV Package Manager") {
        Write-Host "Install UV:"
        Write-Host "  • Using pip: pip install uv"
        Write-Host "  • Or using pipx: pipx install uv"
        Write-Host "  • Or download from: https://github.com/astral-sh/uv"
        Write-Host ""
    }


    if ($script:errors -match "Git") {
        Write-Host "Install Git:"
        Write-Host "  • Download from: https://git-scm.com/download/win"
        Write-Host ""
    }

    if ($script:errors -match "Node.js") {
        Write-Host "Install Node.js:"
        Write-Host "  • Download from: https://nodejs.org/"
        Write-Host ""
    }

    if ($script:errors -match "Jupyter") {
        Write-Host "Install Jupyter:"
        Write-Host "  • Using uv: uv pip install jupyter"
        Write-Host "  • Or using conda: conda install jupyter"
        Write-Host "  • Full instructions: https://jupyter.org/install"
        Write-Host ""
    }

    if ($script:errors -match "Cursor") {
        Write-Host "Install Cursor:"
        Write-Host "  • Download from: https://cursor.sh/"
        Write-Host "  • AI-powered code editor"
        Write-Host ""
    }
}

Write-Host ""
if ($script:errors.Count -eq 0) {
    Write-ColorOutput "[OK] All critical prerequisites are satisfied!" -Type "Success"
    Write-ColorOutput "You can proceed with the setup." -Type "Success"
} else {
    Write-ColorOutput "[X] Some critical prerequisites are missing." -Type "Error"
    Write-ColorOutput "Please install the missing components before proceeding." -Type "Error"
}