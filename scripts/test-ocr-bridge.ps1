# PowerShell wrapper for testing YOLO-CRNN OCR Bridge on local images
param (
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ImagePath,

    [Parameter(Mandatory=$false)]
    [string]$Provider = "crnn_vi_handwriting_v1",

    [Parameter(Mandatory=$false)]
    [string]$BridgeMode = "shadow"
)

$PythonExe = "services\ai-service\.venv\Scripts\python.exe"
$ScriptPath = "services\ai-service\scripts\test_ocr_bridge.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python virtual environment not found at '$PythonExe'."
    exit 1
}

if (-not (Test-Path $ScriptPath)) {
    Write-Error "Bridge diagnostic script not found at '$ScriptPath'."
    exit 1
}

& $PythonExe $ScriptPath $ImagePath --provider $Provider --bridge-mode $BridgeMode
