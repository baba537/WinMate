    # ---------------------------------------------------------------------------
    # WinMate engine. Everything below is identical for every generated script.
    # ---------------------------------------------------------------------------
    $ErrorActionPreference = 'Continue'
    $ProgressPreference = 'SilentlyContinue'
    try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072 } catch {}

    $Self = $MyInvocation.MyCommand.ScriptBlock
    $LogFile = Join-Path $env:TEMP $(if ($Phase) { "WinMate-install-$Phase.log" } else { 'WinMate-install.log' })

    function Write-Step([string]$Text) { Write-Host ''; Write-Host "==> $Text" -ForegroundColor Cyan }
    function Write-Info([string]$Text) { Write-Host "    $Text" -ForegroundColor DarkGray }

    function Test-IsAdmin {
        $id = [Security.Principal.WindowsIdentity]::GetCurrent()
        (New-Object Security.Principal.WindowsPrincipal $id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }

    function Update-SessionPath {
        $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
        $user = [Environment]::GetEnvironmentVariable('Path', 'User')
        $env:Path = (@($machine, $user) | Where-Object { $_ }) -join ';'
    }

    function New-Result($App, [string]$Status, $Code) {
        [pscustomobject]@{ Name = $App.Name; Id = $App.Id; Status = $Status; Code = $Code }
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
            try { Start-Process 'ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1' } catch {}
            return $false
        }
        $script:WingetExtra = @()
        try {
            $v = (& $script:Winget --version) -replace '[^\d\.]', ''
            if ([version]$v -ge [version]'1.4') { $script:WingetExtra = @('--disable-interactivity') }
        } catch {}
        return $true
    }

    function Install-WingetApp($App) {
        $source = if ($App.Source) { $App.Source } else { 'winget' }
        $wargs = @('install', '--id', $App.Id, '--exact', '--source', $source, '--silent',
            '--accept-package-agreements', '--accept-source-agreements') + $script:WingetExtra
        # Start-Process keeps winget's live progress output in the console and returns the real exit code.
        $code = (Start-Process -FilePath $script:Winget -ArgumentList $wargs -NoNewWindow -Wait -PassThru).ExitCode
        switch ($code) {
            0 { return 'installed' }
            -1978335189 { return 'uptodate' }   # APPINSTALLER_CLI_ERROR_UPDATE_NOT_APPLICABLE
            -1978335135 { return 'uptodate' }   # APPINSTALLER_CLI_ERROR_PACKAGE_ALREADY_INSTALLED
            -1978334967 { return 'reboot' }     # APPINSTALLER_CLI_ERROR_INSTALL_REBOOT_REQUIRED_TO_FINISH
            -1978334966 { return 'reboot' }     # APPINSTALLER_CLI_ERROR_INSTALL_REBOOT_REQUIRED_FOR_INSTALL
            3010 { return 'reboot' }
            1641 { return 'reboot' }
            default { return "failed:$code" }
        }
    }

    # --- Scoop ------------------------------------------------------------------
    function Initialize-Scoop {
        if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
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

    function Install-ScoopApp($App) {
        $short = $App.Id.Split('/')[-1]
        $before = scoop prefix $short 6>$null 2>$null
        if ($before -and (Test-Path "$before")) { return 'uptodate' }
        scoop install $App.Id | Out-Host
        $after = scoop prefix $short 6>$null 2>$null
        if ($after -and (Test-Path "$after")) { return 'installed' }
        return 'failed:scoop'
    }

    # --- Chocolatey -------------------------------------------------------------
    function Initialize-Choco {
        if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
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

    function Install-ChocoApp($App) {
        choco install $App.Id -y --no-progress | Out-Host
        switch ($LASTEXITCODE) {
            0 { return 'installed' }
            1641 { return 'reboot' }
            3010 { return 'reboot' }
            default { return "failed:$LASTEXITCODE" }
        }
    }

    # --- Shared -----------------------------------------------------------------
    function Install-AppList($List) {
        $results = @()
        $i = 0
        foreach ($app in $List) {
            $i++
            Write-Step "[$i/$(@($List).Count)] $($app.Name)"
            $status = 'failed'
            for ($attempt = 1; $attempt -le 2; $attempt++) {
                try {
                    $status = switch ($PackageManager) {
                        'winget' { Install-WingetApp $app }
                        'scoop' { Install-ScoopApp $app }
                        'choco' { Install-ChocoApp $app }
                    }
                } catch { $status = "failed:$($_.Exception.Message)" }
                if ($status -notlike 'failed*' -or $status -eq 'failed:-1978335212') { break }  # no retry when the package does not exist
                if ($attempt -eq 1) { Write-Info 'Retrying once...'; Start-Sleep -Seconds 3 }
            }
            $code = if ($status -like 'failed:*') { $status.Substring(7) } else { $null }
            $results += New-Result $app ($status -replace ':.*$', '') $code
        }
        return $results
    }

    function New-PhaseScript([string]$Phase, [string]$ResultFile) {
        $file = Join-Path $env:TEMP ("winmate-" + [guid]::NewGuid().ToString('N') + '.ps1')
        $body = "& {" + $Self.ToString() + "} -Phase '$Phase' -ResultFile '$ResultFile'"
        [IO.File]::WriteAllText($file, $body, (New-Object Text.UTF8Encoding $true))
        return $file
    }

    function Read-PhaseResult([string]$ResultFile, $List) {
        if (Test-Path $ResultFile) {
            $data = @(Get-Content $ResultFile -Raw -Encoding UTF8 | ConvertFrom-Json)
            Remove-Item $ResultFile -Force -ErrorAction SilentlyContinue
            return $data
        }
        return @($List | ForEach-Object { New-Result $_ 'failed' 'no result' })
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
            Write-Warning 'Administrator rights were not granted. Installing without them; some installers may ask on their own.'
            if ($PackageManager -eq 'choco') { return @($List | ForEach-Object { New-Result $_ 'failed' 'admin required' }) }
            return Install-AppList $List
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
        Write-Step 'Installing apps that must not run as administrator'
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
            Write-Warning "Could not start the non-admin installer: $($_.Exception.Message)"
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

    # --- Phases started by the main script --------------------------------------
    if ($Phase) {
        try { Start-Transcript -Path $LogFile -Append | Out-Null } catch {}
        $Host.UI.RawUI.WindowTitle = "WinMate - installing ($Phase)"
        $list = if ($Phase -eq 'user') { @($Apps | Where-Object { $_.NoAdmin }) } else { @($Apps | Where-Object { -not $_.NoAdmin }) }
        $results = @()
        if (Initialize-PackageManager) { $results = Install-AppList $list }
        else { $results = @($list | ForEach-Object { New-Result $_ 'failed' 'package manager missing' }) }
        ConvertTo-Json -InputObject @($results) -Depth 3 | Set-Content -Path $ResultFile -Encoding UTF8
        try { Stop-Transcript | Out-Null } catch {}
        return
    }

    # --- Main -------------------------------------------------------------------
    try { $Host.UI.RawUI.WindowTitle = 'WinMate installer' } catch {}
    try { Start-Transcript -Path $LogFile -Append | Out-Null } catch {}
    Write-Host ''
    Write-Host '  W I N M A T E' -ForegroundColor Cyan
    Write-Host "  Installing $(@($Apps).Count) app(s) with $PackageManager" -ForegroundColor Gray
    Write-Host '  https://winmate.baba537.workers.dev' -ForegroundColor DarkGray

    $results = @()
    $isAdmin = Test-IsAdmin
    $adminApps = @($Apps | Where-Object { -not $_.NoAdmin })
    $userApps = @($Apps | Where-Object { $_.NoAdmin })

    if ($PackageManager -eq 'scoop') {
        if (Initialize-Scoop) { $results += Install-AppList $Apps }
        else { $results += @($Apps | ForEach-Object { New-Result $_ 'failed' 'scoop missing' }) }
    } else {
        if ($PackageManager -eq 'winget' -and -not (Initialize-Winget)) {
            $results += @($Apps | ForEach-Object { New-Result $_ 'failed' 'winget missing' })
            $adminApps = @(); $userApps = @()
        }
        if ($adminApps.Count -gt 0) {
            if ($isAdmin) {
                if (Initialize-PackageManager) { $results += Install-AppList $adminApps }
                else { $results += @($adminApps | ForEach-Object { New-Result $_ 'failed' 'package manager missing' }) }
            } else {
                $results += Invoke-ElevatedPhase $adminApps
            }
        }
        if ($userApps.Count -gt 0) {
            if ($isAdmin) { $results += Invoke-LimitedPhase $userApps } else { $results += Install-AppList $userApps }
        }
    }

    Write-Host ''
    Write-Host '==================== Summary ====================' -ForegroundColor Cyan
    foreach ($r in $results) {
        switch ($r.Status) {
            'installed' { Write-Host "  [OK]      $($r.Name)" -ForegroundColor Green }
            'uptodate' { Write-Host "  [OK]      $($r.Name) (already installed)" -ForegroundColor Green }
            'reboot' { Write-Host "  [REBOOT]  $($r.Name) (restart required)" -ForegroundColor Yellow }
            default { Write-Host "  [FAILED]  $($r.Name)  (code: $($r.Code))" -ForegroundColor Red }
        }
    }
    $failed = @($results | Where-Object { $_.Status -eq 'failed' })
    $ok = @($results).Count - $failed.Count
    Write-Host ''
    Write-Host "  $ok of $(@($results).Count) finished successfully." -ForegroundColor $(if ($failed.Count) { 'Yellow' } else { 'Green' })
    if (@($results | Where-Object { $_.Status -eq 'reboot' }).Count) { Write-Host '  Restart Windows to complete some installations.' -ForegroundColor Yellow }
    if ($failed.Count) { Write-Host "  Re-run the script to retry failed apps. Log: $LogFile" -ForegroundColor DarkGray }
    try { Stop-Transcript | Out-Null } catch {}
    if (-not $NoPause) { Write-Host ''; Read-Host '  Press Enter to close' | Out-Null }
