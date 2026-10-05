# VULCAN - attach the SH-C30G (candleLight/gs_usb) to WSL2 via usbipd-win.
#
# Run in an ELEVATED PowerShell on Windows (usbipd bind needs admin the first time).
# candleLight firmware enumerates as VID:PID 1d50:606f ("Geschwister Schneider CAN").
# If yours is in slcan/serial mode instead it shows as a USB serial (COMx) device -
# reflash to candleLight for native gs_usb, or use slcand in WSL.
#
# Usage:
#   .\src\bringup\attach_can_usb.ps1            # auto-detect 1d50:606f, bind + attach
#   .\src\bringup\attach_can_usb.ps1 -BusId 1-4 # force a specific busid

param([string]$BusId = "")

$ErrorActionPreference = "Stop"

if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
    Write-Error "usbipd not found. Install with: winget install usbipd"
    exit 1
}

if (-not $BusId) {
    Write-Host "Scanning for candleLight (1d50:606f)..."
    $line = (usbipd list) | Select-String "1d50:606f" | Select-Object -First 1
    if (-not $line) {
        Write-Warning "No 1d50:606f device found. Is the SH-C30G plugged in and in candleLight mode?"
        Write-Host "Current devices:"; usbipd list
        exit 1
    }
    $BusId = ($line.ToString().Trim() -split "\s+")[0]
    Write-Host "Found candleLight at busid $BusId"
}

Write-Host "Binding busid $BusId (shared for usbip)..."
usbipd bind --busid $BusId

Write-Host "Attaching busid $BusId to WSL..."
usbipd attach --wsl --busid $BusId

Write-Host ""
Write-Host "Done. In WSL, verify with:"
Write-Host "  dmesg | tail -n 20        # expect: gs_usb ... can0"
Write-Host "  ip link show can0"
Write-Host "  sudo bash src/bringup/bring_up_can.sh can0 500000"
