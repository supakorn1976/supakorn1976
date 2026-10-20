# Build the Modern House in the open IngeTrazo document through AI Bridge (MCP).
# 1. Open IngeTrazo, then Extensions > AI Bridge (MCP)
# 2. Run:  powershell -ExecutionPolicy Bypass -File build_house.ps1
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path 'C:\Program Files\IngeTrazo\ingetrazo-mcp.exe')) {
    Write-Error 'ingetrazo-mcp.exe not found in C:\Program Files\IngeTrazo'
}
$open = (Test-NetConnection 127.0.0.1 -Port 4763 -WarningAction SilentlyContinue).TcpTestSucceeded
if (-not $open) {
    Write-Error 'Port 4763 is closed: open Extensions > AI Bridge (MCP) in IngeTrazo first'
}
python "$here\mcp_call.py" "$here\build_house.json" 2>&1 | Out-String -Width 4000
exit $LASTEXITCODE
