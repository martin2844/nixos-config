$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
@{ computer = $env:COMPUTERNAME; os = $os.Caption; installedAt = (Get-Date -Format o) } | ConvertTo-Json | Set-Content -Encoding UTF8 C:\OEM\ready.json
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    try {
        Copy-Item C:\OEM\ready.json '\\host.lan\Data\Windows-ready.json' -Force
        exit 0
    } catch {
        Start-Sleep -Seconds 2
    }
}
exit 1
