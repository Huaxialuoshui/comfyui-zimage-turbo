[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Prompt,
    [string]$NegativePrompt = '',
    [int]$Width = 512,
    [int]$Height = 512,
    [int]$Seed = 24681357,
    [string]$OutputPrefix = 'qwen21_api',
    [int]$Port = 8188
)

$ErrorActionPreference = 'Stop'
$baseUrl = "http://127.0.0.1:$Port"
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$app = Join-Path $projectRoot 'ComfyUI'
$python = Join-Path $app '.venv\Scripts\python.exe'

try {
    Invoke-RestMethod -Uri "$baseUrl/system_stats" -TimeoutSec 5 | Out-Null
}
catch {
    if (-not (Test-Path -LiteralPath $python)) {
        throw "Unified ComfyUI Python environment not found: $python"
    }

    $logDirectory = Join-Path $projectRoot 'logs\qwen21'
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    $env:KMP_DUPLICATE_LIB_OK = 'TRUE'
    Start-Process `
        -FilePath $python `
        -ArgumentList @('main.py', '--listen', '127.0.0.1', '--port', $Port, '--disable-auto-launch') `
        -WorkingDirectory $app `
        -RedirectStandardOutput (Join-Path $logDirectory 'comfyui.out.log') `
        -RedirectStandardError (Join-Path $logDirectory 'comfyui.err.log') `
        -WindowStyle Hidden | Out-Null

    $deadline = (Get-Date).AddMinutes(2)
    do {
        Start-Sleep -Seconds 2
        try {
            Invoke-RestMethod -Uri "$baseUrl/system_stats" -TimeoutSec 5 | Out-Null
            break
        }
        catch {
            if ((Get-Date) -ge $deadline) {
                throw "Timed out waiting for ComfyUI at $baseUrl"
            }
        }
    } while ($true)
}

$promptGraph = @{
    '1' = @{
        class_type = 'UNETLoader'
        inputs = @{
            unet_name = 'qwen_image_2.1_turbo_int8_convrot.safetensors'
            weight_dtype = 'default'
        }
    }
    '2' = @{
        class_type = 'CLIPLoader'
        inputs = @{
            clip_name = 'qwen3vl_8b_w4a8.safetensors'
            type = 'qwen_image'
            device = 'default'
        }
    }
    '3' = @{
        class_type = 'VAELoader'
        inputs = @{ vae_name = 'qwen_image_2.1_vae_bf16.safetensors' }
    }
    '4' = @{
        class_type = 'QwenImage21Cache'
        inputs = @{
            model = @('1', 0)
            device = 'auto'
            dtype = 'default'
        }
    }
    '5' = @{
        class_type = 'TextEncodeQwenImage21'
        inputs = @{
            clip = @('2', 0)
            prompt = $Prompt
            negative_prompt = $NegativePrompt
            resolution = 1024
        }
    }
    '6' = @{
        class_type = 'EmptyLatentImage'
        inputs = @{
            width = $Width
            height = $Height
            batch_size = 1
        }
    }
    '7' = @{
        class_type = 'ManualSigmas'
        inputs = @{
            sigmas = '1.0, 0.978453, 0.95418, 0.926626, 0.89508, 0.845148, 0.704534, 0.414568, 0'
        }
    }
    '8' = @{
        class_type = 'KSamplerSelect'
        inputs = @{ sampler_name = 'euler' }
    }
    '9' = @{
        class_type = 'RandomNoise'
        inputs = @{ noise_seed = $Seed }
    }
    '10' = @{
        class_type = 'CFGGuider'
        inputs = @{
            model = @('4', 0)
            positive = @('5', 0)
            negative = @('5', 1)
            cfg = 1.0
        }
    }
    '11' = @{
        class_type = 'SamplerCustomAdvanced'
        inputs = @{
            noise = @('9', 0)
            guider = @('10', 0)
            sampler = @('8', 0)
            sigmas = @('7', 0)
            latent_image = @('6', 0)
        }
    }
    '12' = @{
        class_type = 'VAEDecode'
        inputs = @{
            samples = @('11', 0)
            vae = @('3', 0)
        }
    }
    '13' = @{
        class_type = 'SaveImage'
        inputs = @{
            images = @('12', 0)
            filename_prefix = $OutputPrefix
        }
    }
}

$body = @{
    prompt = $promptGraph
    client_id = 'codex-qwen21-api'
} | ConvertTo-Json -Depth 20
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

$queued = Invoke-RestMethod `
    -Uri "$baseUrl/prompt" `
    -Method Post `
    -ContentType 'application/json' `
    -Body $bodyBytes `
    -TimeoutSec 30

if ($queued.node_errors.PSObject.Properties.Count -gt 0) {
    throw ($queued.node_errors | ConvertTo-Json -Depth 10)
}

$promptId = $queued.prompt_id
Write-Host "Queued Qwen-Image 2.1 job: $promptId"

$deadline = (Get-Date).AddMinutes(15)
do {
    Start-Sleep -Seconds 3
    $history = Invoke-RestMethod -Uri "$baseUrl/history/$promptId" -TimeoutSec 20
    $entry = $history.$promptId
} while (-not $entry -and (Get-Date) -lt $deadline)

if (-not $entry) {
    throw "Timed out waiting for prompt $promptId"
}
if ($entry.status.status_str -ne 'success') {
    throw ($entry.status | ConvertTo-Json -Depth 10)
}

$images = $entry.outputs.'13'.images
foreach ($image in $images) {
    $path = Join-Path (Join-Path $app 'output') $image.filename
    Write-Output $path
}
