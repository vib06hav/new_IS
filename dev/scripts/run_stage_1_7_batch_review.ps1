param(
    [string]$PdfDir = "tests/pdfs",
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$reviewRoot = Join-Path $projectRoot ("tests/outputs/stage_1_7_batch_review/" + $timestamp)
$fullRunsHostRoot = Join-Path $reviewRoot "full_runs"
$boundaryRunsHostRoot = Join-Path $reviewRoot "boundary_runs"
$logsRoot = Join-Path $reviewRoot "logs"
$stdoutRoot = Join-Path $reviewRoot "stdout"

New-Item -ItemType Directory -Force -Path $reviewRoot, $fullRunsHostRoot, $boundaryRunsHostRoot, $logsRoot, $stdoutRoot | Out-Null

if ($Rebuild) {
    docker compose up --build -d 2>$null | Out-Host
}

$containerId = (docker compose ps -q api 2>$null).Trim()
if (-not $containerId) {
    throw "Could not resolve the api container id. Start the stack first with 'docker compose up --build -d'."
}

$pdfFiles = Get-ChildItem -Path $PdfDir -Filter *.pdf | Sort-Object Name
if (-not $pdfFiles) {
    throw "No PDF files found in $PdfDir"
}

$summary = @()

function Get-LineValue {
    param(
        [string[]]$Lines,
        [string]$Prefix
    )

    foreach ($line in $Lines) {
        if ($line -like "$Prefix*") {
            return $line.Substring($Prefix.Length).Trim()
        }
    }
    return $null
}

function Copy-ContainerPath {
    param(
        [string]$ContainerId,
        [string]$ContainerRelativePath,
        [string]$DestinationRoot
    )

    if (-not $ContainerRelativePath) {
        return $null
    }

    $normalized = $ContainerRelativePath -replace "\\", "/"
    $leaf = Split-Path $normalized -Leaf
    $dest = Join-Path $DestinationRoot $leaf
    docker cp "${ContainerId}:/app/$normalized" $dest 2>$null | Out-Null
    return $dest
}

foreach ($pdf in $pdfFiles) {
    $safeName = [IO.Path]::GetFileNameWithoutExtension($pdf.Name).Replace(" ", "_").Replace("(", "").Replace(")", "")
    $containerPdfPath = "tests/pdfs/$($pdf.Name)"
    $startedAt = (Get-Date).ToUniversalTime().ToString("o")

    $runOutput = & docker compose exec api python scripts/run_stage_1_7_pipeline_debug.py --pdf $containerPdfPath 2>$null
    $runExitCode = $LASTEXITCODE
    $endedAt = (Get-Date).ToUniversalTime().ToString("o")

    $stdoutFile = Join-Path $stdoutRoot ($safeName + "_pipeline_stdout.txt")
    $runOutput | Out-File -FilePath $stdoutFile -Encoding utf8

    $apiLogFile = Join-Path $logsRoot ($safeName + "_api.log")
    docker compose logs api --since $startedAt --until $endedAt 2>$null | Out-File -FilePath $apiLogFile -Encoding utf8

    $fullRunDir = Get-LineValue -Lines $runOutput -Prefix "Run directory: "
    $applicationId = Get-LineValue -Lines $runOutput -Prefix "Application ID: "
    $uploadStatus = Get-LineValue -Lines $runOutput -Prefix "Upload status: "
    $pipelineStatus = Get-LineValue -Lines $runOutput -Prefix "Pipeline status: "
    $policyPassed = Get-LineValue -Lines $runOutput -Prefix "Policy passed: "

    $copiedFullRunDir = Copy-ContainerPath -ContainerId $containerId -ContainerRelativePath $fullRunDir -DestinationRoot $fullRunsHostRoot

    $boundaryRunDir = $null
    $copiedBoundaryRunDir = $null

    if ($applicationId -and $policyPassed -ne "True") {
        $boundaryStartedAt = (Get-Date).ToUniversalTime().ToString("o")
        $boundaryOutput = & docker compose exec api python scripts/run_stage_1_7_boundary_debug.py --application-id $applicationId 2>$null
        $boundaryExitCode = $LASTEXITCODE
        $boundaryEndedAt = (Get-Date).ToUniversalTime().ToString("o")

        $boundaryStdoutFile = Join-Path $stdoutRoot ($safeName + "_boundary_stdout.txt")
        $boundaryOutput | Out-File -FilePath $boundaryStdoutFile -Encoding utf8

        $boundaryLogFile = Join-Path $logsRoot ($safeName + "_boundary_api.log")
        docker compose logs api --since $boundaryStartedAt --until $boundaryEndedAt 2>$null | Out-File -FilePath $boundaryLogFile -Encoding utf8

        $boundaryRunDir = Get-LineValue -Lines $boundaryOutput -Prefix "Run directory: "
        $copiedBoundaryRunDir = Copy-ContainerPath -ContainerId $containerId -ContainerRelativePath $boundaryRunDir -DestinationRoot $boundaryRunsHostRoot
    }
    else {
        $boundaryExitCode = $null
    }

    $summary += [ordered]@{
        pdf_name = $pdf.Name
        pipeline_exit_code = $runExitCode
        upload_status = $uploadStatus
        pipeline_status = $pipelineStatus
        policy_passed = $policyPassed
        application_id = $applicationId
        full_run_container_dir = $fullRunDir
        full_run_host_dir = $copiedFullRunDir
        boundary_exit_code = $boundaryExitCode
        boundary_run_container_dir = $boundaryRunDir
        boundary_run_host_dir = $copiedBoundaryRunDir
        pipeline_stdout = $stdoutFile
        api_log = $apiLogFile
    }

    Write-Host "$($pdf.Name): upload=$uploadStatus pipeline=$pipelineStatus policy=$policyPassed"
}

$summaryJson = Join-Path $reviewRoot "summary.json"
$summary | ConvertTo-Json -Depth 4 | Out-File -FilePath $summaryJson -Encoding utf8

$summaryCsv = Join-Path $reviewRoot "summary.csv"
$summary | Export-Csv -Path $summaryCsv -NoTypeInformation

Write-Host ""
Write-Host "Review root: $reviewRoot"
Write-Host "Summary JSON: $summaryJson"
Write-Host "Summary CSV: $summaryCsv"
