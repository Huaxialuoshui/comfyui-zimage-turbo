[CmdletBinding()]
param(
    [string]$ComfyUIRoot = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $ComfyUIRoot) {
    $ComfyUIRoot = Join-Path $projectRoot 'ComfyUI'
}

$downloads = @(
    [ordered]@{
        Name = 'Qwen-Image 2.1 Turbo INT8'
        RelativePath = 'models\diffusion_models\qwen_image_2.1_turbo_int8_convrot.safetensors'
        Url = 'https://modelscope.cn/models/Comfy-Org/Qwen-Image-2.1/resolve/master/diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors'
        ExpectedBytes = 7256787829L
    },
    [ordered]@{
        Name = 'Qwen3-VL 8B W4A8 text encoder'
        RelativePath = 'models\text_encoders\qwen3vl_8b_w4a8.safetensors'
        Url = 'https://modelscope.cn/models/Comfy-Org/Qwen-Image-2.1/resolve/master/text_encoders/qwen3vl_8b_w4a8.safetensors'
        ExpectedBytes = 6312105364L
    },
    [ordered]@{
        Name = 'Qwen-Image 2.1 VAE'
        RelativePath = 'models\vae\qwen_image_2.1_vae_bf16.safetensors'
        Url = 'https://modelscope.cn/models/Comfy-Org/Qwen-Image-2.1/resolve/master/vae/qwen_image_2.1_vae_bf16.safetensors'
        ExpectedBytes = 675509688L
    }
)

$curl = Get-Command curl.exe -ErrorAction Stop
$logDirectory = Join-Path $projectRoot 'logs\qwen21-download'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

$jobs = foreach ($item in $downloads) {
    $target = Join-Path $ComfyUIRoot $item.RelativePath
    $parent = Split-Path -Parent $target
    New-Item -ItemType Directory -Path $parent -Force | Out-Null

    if ((Test-Path -LiteralPath $target) -and
        (Get-Item -LiteralPath $target).Length -eq $item.ExpectedBytes) {
        Write-Host "Already complete: $target"
        continue
    }

    if (Test-Path -LiteralPath $target) {
        throw "A partial or unexpected file already exists at $target. Refusing to overwrite it."
    }

    $part = "$target.part"
    $stdout = Join-Path $logDirectory (($item.RelativePath -replace '[\\/:*?"<>|]', '_') + '.out.log')
    $stderr = Join-Path $logDirectory (($item.RelativePath -replace '[\\/:*?"<>|]', '_') + '.err.log')

    $arguments = @(
        '-L',
        '--fail',
        '--retry', '8',
        '--retry-delay', '3',
        '--retry-all-errors',
        '-C', '-',
        '-A', 'Mozilla/5.0',
        '--output', $part,
        $item.Url
    )

    $process = Start-Process `
        -FilePath $curl.Source `
        -ArgumentList $arguments `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -WindowStyle Hidden `
        -PassThru

    [pscustomobject]@{
        Item = $item
        Target = $target
        Part = $part
        Process = $process
        StdErr = $stderr
    }
}

if (-not $jobs) {
    Write-Host 'All model files are already present.'
    exit 0
}

while ($true) {
    $active = @($jobs | Where-Object { -not $_.Process.HasExited })
    foreach ($job in $jobs) {
        $displayName = $job.Item.Name
        $existingBytes = if (Test-Path -LiteralPath $job.Part) {
            (Get-Item -LiteralPath $job.Part).Length
        }
        else {
            0L
        }
        $percent = [math]::Round(($existingBytes / $job.Item.ExpectedBytes) * 100, 1)
        Write-Host ('{0}: {1:N2} / {2:N2} GiB ({3}%)' -f `
            $displayName,
            ($existingBytes / 1GB),
            ($job.Item.ExpectedBytes / 1GB),
            $percent)
    }

    if ($active.Count -eq 0) {
        break
    }
    Start-Sleep -Seconds 10
}

$failed = @()
foreach ($job in $jobs) {
    $job.Process.Refresh()
    if ($null -ne $job.Process.ExitCode -and $job.Process.ExitCode -ne 0) {
        $errorText = if (Test-Path -LiteralPath $job.StdErr) {
            Get-Content -LiteralPath $job.StdErr -Tail 8 | Out-String
        }
        else {
            'No curl error log was produced.'
        }
        $failed += "$($job.Item.Name): exit $($job.Process.ExitCode)`n$errorText"
        continue
    }

    $actualBytes = (Get-Item -LiteralPath $job.Part).Length
    if ($actualBytes -ne $job.Item.ExpectedBytes) {
        $failed += "$($job.Item.Name): expected $($job.Item.ExpectedBytes) bytes, got $actualBytes"
        continue
    }

    Move-Item -LiteralPath $job.Part -Destination $job.Target
    Write-Host "Placed: $($job.Target)"
}

if ($failed) {
    $failed | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host 'All Qwen-Image 2.1 model files downloaded and verified by byte size.'
