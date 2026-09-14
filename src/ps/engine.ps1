    # ---------------------------------------------------------------------------
    # WinMate engine __WINMATE_VERSION__
    # Identical in every generated script. Verify it with: winmate.ps1 -Verify <file>
    # Source: https://github.com/baba537/WinMate/blob/main/src/ps/engine.ps1
    # ---------------------------------------------------------------------------
    $ErrorActionPreference = 'Continue'
    $ProgressPreference = 'SilentlyContinue'
    try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072 } catch {}

    if (-not $Mode) { $Mode = 'install' }
    $DryRun = [bool]$DryRun
    $RestorePoint = [bool]$RestorePoint
    if (-not $RunId) { $RunId = Get-Date -Format 'yyyyMMdd-HHmmss' }
    $Self = $MyInvocation.MyCommand.ScriptBlock
    $DataDir = Join-Path $env:LOCALAPPDATA 'WinMate'
    $LogDir = Join-Path $DataDir 'logs'
    New-Item -ItemType Directory -Force -Path $LogDir, (Join-Path $DataDir 'runs') -ErrorAction SilentlyContinue | Out-Null
    $LogFile = Join-Path $LogDir $(if ($Phase) { "$RunId-$Phase.log" } else { "$RunId.log" })
    $ModeVerb = @{ install = 'Installing'; upgrade = 'Updating'; uninstall = 'Removing' }[$Mode]

    if ($Proxy) {
        $env:HTTP_PROXY = $Proxy
        $env:HTTPS_PROXY = $Proxy
        try { [Net.WebRequest]::DefaultWebProxy = New-Object Net.WebProxy($Proxy, $true) } catch {}
    }

    function Write-Step([string]$Text) { Write-Host ''; Write-Host "==> $Text" -ForegroundColor Cyan }
    function Write-Info([string]$Text) { Write-Host "    $Text" -ForegroundColor DarkGray }

    function Test-IsAdmin {
        $id = [Security.Principal.WindowsIdentity]::GetCurrent()
        (New-Object Security.Principal.WindowsPrincipal $id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }

    function Test-PendingReboot {
        foreach ($key in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending',
                'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')) {
            if (Test-Path $key) { return $true }
        }
        return $false
    }

    function Update-SessionPath {
        $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
        $user = [Environment]::GetEnvironmentVariable('Path', 'User')
        $env:Path = (@($machine, $user) | Where-Object { $_ }) -join ';'
    }

    function New-Result($App, [string]$Status, $Code, $Detail) {
        [pscustomobject]@{ Name = $App.Name; Id = $App.Id; Status = $Status; Code = $Code; Detail = $Detail }
    }

    function New-RestorePoint {
        if (-not $RestorePoint -or $DryRun) { return }
        Write-Step 'Creating a System Restore point'
        try {
            Checkpoint-Computer -Description "WinMate $Mode ($(@($Apps).Count) apps)" -RestorePointType 'APPLICATION_INSTALL' -ErrorAction Stop -WarningVariable rpWarning 3>$null
            if ($rpWarning) { Write-Warning "$rpWarning" } else { Write-Info 'Restore point created.' }
        } catch {
            Write-Warning "No restore point was created: $($_.Exception.Message) (System Protection may be turned off)."
        }
    }

    # --- winget -----------------------------------------------------------------
    function Get-WingetPath {
        $cmd = Get-Command winget.exe -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
        # App Installer is present on every Windows 10/11 but may not be registered yet on a fresh install.
        try { Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe -ErrorAction Stop; Start-Sleep -Seconds 3 } catch {}
        $cmd = Get-Command winget.exe -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
        # Elevated sessions of another account do not have the per-user alias; use the package directly.
        $exe = Get-ChildItem "$env:ProgramFiles\WindowsApps\Microsoft.DesktopAppInstaller_*_x64__8wekyb3d8bbwe\winget.exe" -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending | Select-Object -First 1
        if ($exe) { return $exe.FullName }
        return $null
    }

    function Initialize-Winget {
        $script:Winget = Get-WingetPath
        if (-not $script:Winget) {
            Write-Host ''
            Write-Host 'winget (App Installer) was not found on this PC.' -ForegroundColor Red
            Write-Host 'Install or update "App Installer" from the Microsoft Store, then run this script again.' -ForegroundColor Yellow
            Write-Host 'https://aka.ms/getwinget' -ForegroundColor Yellow
            if (-not $DryRun) { try { Start-Process 'ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1' } catch {} }
            return $false
        }
        $script:WingetExtra = @()
        $script:WingetProxy = $false
        try {
            $v = (& $script:Winget --version) -replace '[^\d\.]', ''
            if ([version]$v -ge [version]'1.4') { $script:WingetExtra = @('--disable-interactivity') }
        } catch {}
        if ($Proxy) {
            # winget only accepts --proxy when an administrator enabled it; otherwise it uses the Windows proxy settings.
            try { $script:WingetProxy = [bool]((& $script:Winget settings export | ConvertFrom-Json).adminSettings.ProxyCommandLineOptions) } catch {}
            if (-not $script:WingetProxy) { Write-Info 'winget uses the Windows proxy settings (the --proxy option is disabled by policy).' }
        }
        return $true
    }

    function Test-WingetInstalled($App) {
        $extra = $script:WingetExtra
        & $script:Winget list --id $App.Id --exact --accept-source-agreements @extra 2>&1 | Out-Null
        return $LASTEXITCODE -eq 0
    }

    function Invoke-WingetApp($App) {
        $source = if ($App.Source) { $App.Source } else { 'winget' }
        $action = $Mode
        $wasInstalled = $false
        if ($Mode -eq 'install') { $wasInstalled = Test-WingetInstalled $App }
        $wargs = @($action, '--id', $App.Id, '--exact', '--source', $source, '--silent', '--accept-source-agreements')
        if ($action -ne 'uninstall') { $wargs += '--accept-package-agreements' }
        if ($action -eq 'install' -and $App.Version) { $wargs += @('--version', $App.Version) }
        if ($script:WingetProxy) { $wargs += @('--proxy', $Proxy) }
        $wargs += $script:WingetExtra
        # Start-Process keeps winget's live progress output in the console and returns the real exit code.
        # winget verifies the SHA-256 hash of every installer against its manifest before running it.
        $code = (Start-Process -FilePath $script:Winget -ArgumentList $wargs -NoNewWindow -Wait -PassThru).ExitCode
        switch ($code) {
            0 {
                if ($Mode -eq 'install') { if ($wasInstalled) { return 'updated' } else { return 'installed' } }
                if ($Mode -eq 'upgrade') { return 'updated' }
                return 'removed'
            }
            -1978335189 { return 'uptodate' }   # APPINSTALLER_CLI_ERROR_UPDATE_NOT_APPLICABLE
            -1978335135 { return 'uptodate' }   # APPINSTALLER_CLI_ERROR_PACKAGE_ALREADY_INSTALLED
            -1978334967 { if ($wasInstalled) { return 'reboot-updated' } else { return 'reboot' } }  # ..._REBOOT_REQUIRED_TO_FINISH
            -1978334966 { if ($wasInstalled) { return 'reboot-updated' } else { return 'reboot' } }  # ..._REBOOT_REQUIRED_FOR_INSTALL
            3010 { if ($wasInstalled) { return 'reboot-updated' } else { return 'reboot' } }
            1641 { if ($wasInstalled) { return 'reboot-updated' } else { return 'reboot' } }
            -1978335212 { if ($Mode -eq 'install') { return 'failed:-1978335212' } else { return 'notinstalled' } }  # no package found
            default { return "failed:$code" }
        }
    }

    # --- Scoop ------------------------------------------------------------------
    function Initialize-Scoop {
        if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
            if ($DryRun -or $Mode -ne 'install') { Write-Info 'Scoop is not installed.'; return $false }
            Write-Step 'Installing Scoop'
            $policy = Get-ExecutionPolicy -Scope CurrentUser
            if ($policy -in @('Restricted', 'Undefined', 'AllSigned')) {
                try { Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction Stop } catch {}
            }
            $installer = Invoke-RestMethod -Uri 'https://get.scoop.sh'
            if (Test-IsAdmin) { & ([scriptblock]::Create($installer)) -RunAsAdmin | Out-Host } else { & ([scriptblock]::Create($installer)) | Out-Host }
            $env:Path = "$env:USERPROFILE\scoop\shims;$env:Path"
        }
        if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
            Write-Host 'Scoop could not be installed. See https://scoop.sh' -ForegroundColor Red
            return $false
        }
        if ($DryRun -or $Mode -eq 'uninstall') { return $true }
        if ($Buckets.Count -gt 0 -and -not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Step 'Installing Git (needed for Scoop buckets)'
            scoop install main/git | Out-Host
        }
        $known = @(scoop bucket list | ForEach-Object { if ($_.Name) { $_.Name } else { "$_" } })
        foreach ($bucket in $Buckets) {
            if ($known -notcontains $bucket) { Write-Step "Adding Scoop bucket '$bucket'"; scoop bucket add $bucket | Out-Host }
        }
        return $true
    }

    function Test-ScoopInstalled($App) {
        $prefix = scoop prefix ($App.Id.Split('/')[-1]) 6>$null 2>$null
        return [bool]($prefix -and (Test-Path "$prefix"))
    }

    function Invoke-ScoopApp($App) {
        $short = $App.Id.Split('/')[-1]
        $present = Test-ScoopInstalled $App
        switch ($Mode) {
            'install' {
                if ($present) { return 'uptodate' }
                scoop install $App.Id | Out-Host
                if (Test-ScoopInstalled $App) { return 'installed' } else { return 'failed:scoop' }
            }
            'upgrade' {
                if (-not $present) { return 'notinstalled' }
                scoop update $short | Out-Host
                return 'updated'
            }
            'uninstall' {
                if (-not $present) { return 'notinstalled' }
                scoop uninstall $short | Out-Host
                if (Test-ScoopInstalled $App) { return 'failed:scoop' } else { return 'removed' }
            }
        }
    }

    # --- Chocolatey -------------------------------------------------------------
    function Initialize-Choco {
        if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
            if ($DryRun -or $Mode -ne 'install') { Write-Info 'Chocolatey is not installed.'; return $false }
            Write-Step 'Installing Chocolatey'
            Set-ExecutionPolicy Bypass -Scope Process -Force
            Invoke-Expression ((New-Object Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')) | Out-Host
            Update-SessionPath
            $env:Path += ";$env:ALLUSERSPROFILE\chocolatey\bin"
        }
        if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
            Write-Host 'Chocolatey could not be installed. See https://chocolatey.org/install' -ForegroundColor Red
            return $false
        }
        return $true
    }

    function Test-ChocoInstalled($App) {
        $local = @(choco list $App.Id --exact --limit-output 2>$null)
        return $local.Count -gt 0 -and "$($local[0])" -like "$($App.Id)|*"
    }

    function Invoke-ChocoApp($App) {
        $wasInstalled = Test-ChocoInstalled $App
        if ($Mode -eq 'install' -and $wasInstalled) { return 'uptodate' }
        if ($Mode -ne 'install' -and -not $wasInstalled) { return 'notinstalled' }
        $cargs = @($Mode, $App.Id, '-y', '--no-progress')
        if ($Mode -eq 'install' -and $App.Version) { $cargs += "--version=$($App.Version)" }
        if ($Proxy) { $cargs += "--proxy=$Proxy" }
        choco @cargs | Out-Host
        $code = $LASTEXITCODE
        if ($code -in @(1641, 3010)) { return 'reboot' }
        if ($code -ne 0) { return "failed:$code" }
        return @{ install = 'installed'; upgrade = 'updated'; uninstall = 'removed' }[$Mode]
    }

    # --- Dry run ------------------------------------------------------------------
    function Get-AppPlan($App) {
        $installed = $false; $available = $true; $version = $null
        switch ($PackageManager) {
            'winget' {
                $installed = Test-WingetInstalled $App
                $source = if ($App.Source) { $App.Source } else { 'winget' }
                $extra = $script:WingetExtra
                $show = & $script:Winget show --id $App.Id --exact --source $source --accept-source-agreements @extra 2>&1 | Out-String
                $available = $LASTEXITCODE -eq 0
                if ($show -match '(?m)^\s*Version:\s*(\S+)') { $version = $Matches[1] }
            }
            'scoop' { $installed = Test-ScoopInstalled $App }
            'choco' {
                $installed = Test-ChocoInstalled $App
                $remote = @(choco search $App.Id --exact --limit-output 2>$null)
                $available = $remote.Count -gt 0
                if ($available) { $version = "$($remote[0])".Split('|')[-1] }
            }
        }
        if ($App.Version) { $version = "$($App.Version) (pinned)" }
        if ($Mode -eq 'install') {
            if (-not $available) { return New-Result $App 'plan-missing' $null 'package not found' }
            if ($installed) { return New-Result $App 'plan-skip' $null 'already installed - would update if a newer version exists' }
            return New-Result $App 'plan-install' $null $version
        }
        if (-not $installed) { return New-Result $App 'plan-skip' $null 'not installed' }
        return New-Result $App "plan-$Mode" $null $version
    }

    # --- Shared -----------------------------------------------------------------
    function Invoke-AppList($List) {
        $results = @()
        $i = 0
        foreach ($app in $List) {
            $i++
            Write-Step "[$i/$(@($List).Count)] $ModeVerb $($app.Name)"
            $status = 'failed'
            for ($attempt = 1; $attempt -le 2; $attempt++) {
                try {
                    $status = switch ($PackageManager) {
                        'winget' { Invoke-WingetApp $app }
                        'scoop' { Invoke-ScoopApp $app }
                        'choco' { Invoke-ChocoApp $app }
                    }
                } catch { $status = "failed:$($_.Exception.Message)" }
                if ($status -notlike 'failed*' -or $status -eq 'failed:-1978335212') { break }  # no retry when the package does not exist
                if ($attempt -eq 1) { Write-Info 'Retrying once...'; Start-Sleep -Seconds 3 }
            }
            $code = if ($status -like 'failed:*') { $status.Substring(7) } else { $null }
            $results += New-Result $app ($status -replace ':.*$', '') $code $null
        }
        return $results
    }

    function ConvertTo-PsLiteral([string]$Value) { "'" + ($Value -replace "'", "''") + "'" }

    function New-ScriptText([string]$NewMode, $List) {
        # Rebuilds this script with a different configuration (used for the undo script).
        $lines = @(
            '    # >>> config',
            "    `$PackageManager = $(ConvertTo-PsLiteral $PackageManager)",
            "    `$Mode = $(ConvertTo-PsLiteral $NewMode)",
            '    $DryRun = $false',
            '    $RestorePoint = $false',
            "    `$Proxy = $(ConvertTo-PsLiteral $Proxy)",
            "    `$Buckets = @($((@($Buckets) | ForEach-Object { ConvertTo-PsLiteral $_ }) -join ', '))",
            '    $Apps = @('
        )
        foreach ($a in $List) {
            $parts = @("Name = $(ConvertTo-PsLiteral $a.Name)", "Id = $(ConvertTo-PsLiteral $a.Id)")
            if ($a.Source) { $parts += "Source = $(ConvertTo-PsLiteral $a.Source)" }
            if ($a.NoAdmin) { $parts += 'NoAdmin = $true' }
            $lines += "        @{ $($parts -join '; ') }"
        }
        $lines += @('    )', '    # <<< config')
        $config = $lines -join "`n"
        # Replace only the first (real) config block; the same markers appear as text in this function.
        $pattern = New-Object Text.RegularExpressions.Regex '(?s)[ \t]*# >>> config.*?# <<< config'
        $inner = $pattern.Replace($Self.ToString(), [Text.RegularExpressions.MatchEvaluator] { param($m) $config }, 1)
        return "# WinMate undo script - generated $(Get-Date -Format s) for run $RunId`n& {" + $inner + "}`n"
    }

    function Save-RunRecord($Results) {
        $record = [ordered]@{
            id = $RunId; date = (Get-Date).ToString('s'); packageManager = $PackageManager; mode = $Mode
            dryRun = $DryRun; log = $LogFile; results = @($Results)
        }
        $file = Join-Path $DataDir "runs\$RunId.json"
        ConvertTo-Json -InputObject $record -Depth 4 | Set-Content -Path $file -Encoding UTF8
        if ($Mode -ne 'install' -or $DryRun) { return $null }
        # Only apps that were not installed before this run go into the undo script.
        $new = @($Results | Where-Object { $_.Status -in @('installed', 'reboot') } | ForEach-Object { $_.Id })
        if (-not $new.Count) { return $null }
        $undoApps = @($Apps | Where-Object { $new -contains $_.Id })
        $undo = Join-Path $DataDir "runs\$RunId-undo.ps1"
        [IO.File]::WriteAllText($undo, (New-ScriptText 'uninstall' $undoApps), (New-Object Text.UTF8Encoding $true))
        return $undo
    }

    function New-PhaseScript([string]$Phase, [string]$ResultFile) {
        $file = Join-Path $env:TEMP ("winmate-" + [guid]::NewGuid().ToString('N') + '.ps1')
        $body = "& {" + $Self.ToString() + "} -Phase '$Phase' -ResultFile '$ResultFile' -RunId '$RunId'"
        [IO.File]::WriteAllText($file, $body, (New-Object Text.UTF8Encoding $true))
        return $file
    }

    function Read-PhaseResult([string]$ResultFile, $List) {
        if (Test-Path $ResultFile) {
            $data = @(Get-Content $ResultFile -Raw -Encoding UTF8 | ConvertFrom-Json)
            Remove-Item $ResultFile -Force -ErrorAction SilentlyContinue
            return $data
        }
        return @($List | ForEach-Object { New-Result $_ 'failed' 'no result' $null })
    }

    function Invoke-ElevatedPhase($List) {
        $resultFile = Join-Path $env:TEMP ("winmate-" + [guid]::NewGuid().ToString('N') + '.json')
        $file = New-PhaseScript 'admin' $resultFile
        Write-Step 'Requesting administrator rights once for all installers'
        Write-Info 'Confirm the Windows prompt. Progress continues in the new administrator window.'
        try {
            $p = Start-Process -FilePath 'powershell.exe' -Verb RunAs -Wait -PassThru `
                -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$file`"")
        } catch {
            Remove-Item $file -Force -ErrorAction SilentlyContinue
            Write-Warning 'Administrator rights were not granted. Continuing without them; some installers may ask on their own.'
            if ($PackageManager -eq 'choco') { return @($List | ForEach-Object { New-Result $_ 'failed' 'admin required' $null }) }
            return Invoke-AppList $List
        }
        Remove-Item $file -Force -ErrorAction SilentlyContinue
        return Read-PhaseResult $resultFile $List
    }

    function Invoke-LimitedPhase($List) {
        # A few installers (e.g. Spotify) refuse to run as administrator.
        # From an elevated session, start them as the signed-in user via a one-time scheduled task.
        $resultFile = Join-Path $env:TEMP ("winmate-" + [guid]::NewGuid().ToString('N') + '.json')
        $file = New-PhaseScript 'user' $resultFile
        $task = 'WinMate-' + [guid]::NewGuid().ToString('N')
        Write-Step 'Handling apps that must not run as administrator'
        try {
            $user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
            $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$file`""
            $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
            Register-ScheduledTask -TaskName $task -Action $action -Principal $principal -Force | Out-Null
            Start-ScheduledTask -TaskName $task
            $waited = 0
            while (-not (Test-Path $resultFile) -and $waited -lt 3600) {
                Start-Sleep -Seconds 2; $waited += 2
                $state = (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue).State
                if ($waited -gt 10 -and $state -ne 'Running') { break }
            }
        } catch {
            Write-Warning "Could not start the non-admin task: $($_.Exception.Message)"
        } finally {
            Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
            Remove-Item $file -Force -ErrorAction SilentlyContinue
        }
        return Read-PhaseResult $resultFile $List
    }

    function Initialize-PackageManager {
        switch ($PackageManager) {
            'winget' { return Initialize-Winget }
            'scoop' { return Initialize-Scoop }
            'choco' { return Initialize-Choco }
        }
    }

    function Write-Summary($Results) {
        Write-Host ''
        Write-Host '==================== Summary ====================' -ForegroundColor Cyan
        foreach ($r in $Results) {
            $detail = if ($r.Detail) { "  ($($r.Detail))" } else { '' }
            switch ($r.Status) {
                'installed' { Write-Host "  [OK]       $($r.Name) installed" -ForegroundColor Green }
                'updated' { Write-Host "  [OK]       $($r.Name) updated" -ForegroundColor Green }
                'removed' { Write-Host "  [OK]       $($r.Name) removed" -ForegroundColor Green }
                'uptodate' { Write-Host "  [OK]       $($r.Name) already up to date" -ForegroundColor Green }
                'notinstalled' { Write-Host "  [SKIPPED]  $($r.Name) is not installed" -ForegroundColor DarkGray }
                { $_ -like 'reboot*' } { Write-Host "  [REBOOT]   $($r.Name) needs a restart to finish" -ForegroundColor Yellow }
                'plan-install' { Write-Host "  [PLAN]     install $($r.Name)$detail" -ForegroundColor Cyan }
                'plan-upgrade' { Write-Host "  [PLAN]     update $($r.Name)$detail" -ForegroundColor Cyan }
                'plan-uninstall' { Write-Host "  [PLAN]     remove $($r.Name)$detail" -ForegroundColor Cyan }
                'plan-skip' { Write-Host "  [PLAN]     skip $($r.Name)$detail" -ForegroundColor DarkGray }
                'plan-missing' { Write-Host "  [MISSING]  $($r.Name)$detail" -ForegroundColor Red }
                default { Write-Host "  [FAILED]   $($r.Name)  (code: $($r.Code))" -ForegroundColor Red }
            }
        }
    }

    # --- Phases started by the main script --------------------------------------
    if ($Phase -eq 'selftest') {
        # Used by tools/test_script.py: writes the undo script for all apps without installing anything.
        [IO.File]::WriteAllText($ResultFile, (New-ScriptText 'uninstall' $Apps), (New-Object Text.UTF8Encoding $false))
        return
    }
    if ($Phase) {
        try { Start-Transcript -Path $LogFile -Append | Out-Null } catch {}
        try { $Host.UI.RawUI.WindowTitle = "WinMate - $ModeVerb ($Phase)" } catch {}
        $list = if ($Phase -eq 'user') { @($Apps | Where-Object { $_.NoAdmin }) } else { @($Apps | Where-Object { -not $_.NoAdmin }) }
        $results = @()
        if (Initialize-PackageManager) {
            if ($Phase -eq 'admin') { New-RestorePoint }
            $results = Invoke-AppList $list
        } else { $results = @($list | ForEach-Object { New-Result $_ 'failed' 'package manager missing' $null }) }
        ConvertTo-Json -InputObject @($results) -Depth 3 | Set-Content -Path $ResultFile -Encoding UTF8
        try { Stop-Transcript | Out-Null } catch {}
        return
    }

    # --- Main -------------------------------------------------------------------
    try { $Host.UI.RawUI.WindowTitle = 'WinMate' } catch {}
    try { Start-Transcript -Path $LogFile -Append | Out-Null } catch {}
    Write-Host ''
    Write-Host '  W I N M A T E  __WINMATE_VERSION__' -ForegroundColor Cyan
    Write-Host "  $(if ($DryRun) { 'Dry run: ' })$ModeVerb $(@($Apps).Count) app(s) with $PackageManager" -ForegroundColor Gray
    Write-Host '  https://winmate.baba537.workers.dev' -ForegroundColor DarkGray

    $results = @()
    $isAdmin = Test-IsAdmin

    if ($DryRun) {
        Write-Info 'Nothing will be changed. Checking what would happen...'
        if (Initialize-PackageManager) {
            foreach ($app in $Apps) { Write-Info "Checking $($app.Name)"; $results += Get-AppPlan $app }
        } else {
            $results = @($Apps | ForEach-Object { New-Result $_ 'plan-install' $null "$PackageManager would be installed first" })
        }
    } else {
        if (Test-PendingReboot) { Write-Warning 'Windows has a pending restart. Some installers may fail until you restart.' }
        $adminApps = @($Apps | Where-Object { -not $_.NoAdmin })
        $userApps = @($Apps | Where-Object { $_.NoAdmin })

        if ($PackageManager -eq 'scoop') {
            if ($RestorePoint) { Write-Info 'Restore points need administrator rights and are skipped for Scoop.' }
            if (Initialize-Scoop) { $results += Invoke-AppList $Apps }
            else { $results += @($Apps | ForEach-Object { New-Result $_ 'failed' 'scoop missing' $null }) }
        } else {
            if ($PackageManager -eq 'winget' -and -not (Initialize-Winget)) {
                $results += @($Apps | ForEach-Object { New-Result $_ 'failed' 'winget missing' $null })
                $adminApps = @(); $userApps = @()
            }
            if ($adminApps.Count -gt 0) {
                if ($isAdmin) {
                    if (Initialize-PackageManager) { New-RestorePoint; $results += Invoke-AppList $adminApps }
                    else { $results += @($adminApps | ForEach-Object { New-Result $_ 'failed' 'package manager missing' $null }) }
                } else {
                    $results += Invoke-ElevatedPhase $adminApps
                }
            }
            if ($userApps.Count -gt 0) {
                if ($isAdmin) { $results += Invoke-LimitedPhase $userApps } else { $results += Invoke-AppList $userApps }
            }
        }
    }

    Write-Summary $results
    $failed = @($results | Where-Object { $_.Status -eq 'failed' })
    $needsReboot = @($results | Where-Object { $_.Status -like 'reboot*' }).Count -gt 0
    Write-Host ''
    if ($DryRun) {
        Write-Host '  Dry run finished - nothing was changed.' -ForegroundColor Green
    } else {
        $ok = @($results).Count - $failed.Count
        Write-Host "  $ok of $(@($results).Count) finished successfully." -ForegroundColor $(if ($failed.Count) { 'Yellow' } else { 'Green' })
        if ($failed.Count) { Write-Host '  Run the script again to retry the failed apps.' -ForegroundColor DarkGray }
    }
    $undo = $null
    try { $undo = Save-RunRecord $results } catch { Write-Warning "Could not save the run record: $($_.Exception.Message)" }
    Write-Host "  Log: $LogFile" -ForegroundColor DarkGray
    if ($undo) {
        Write-Host '  To uninstall the apps this run added:' -ForegroundColor DarkGray
        Write-Host "  powershell -ExecutionPolicy Bypass -File `"$undo`"" -ForegroundColor DarkGray
    }
    try { Stop-Transcript | Out-Null } catch {}
    if (-not $NoPause) {
        Write-Host ''
        if ($needsReboot) {
            $answer = Read-Host '  Some apps need a restart. Restart Windows now? (y/N)'
            if ($answer -match '^(y|j)') { Restart-Computer -Force }
        } else {
            Read-Host '  Press Enter to close' | Out-Null
        }
    } elseif ($needsReboot) {
        Write-Host '  Restart Windows to finish the installation.' -ForegroundColor Yellow
    }
