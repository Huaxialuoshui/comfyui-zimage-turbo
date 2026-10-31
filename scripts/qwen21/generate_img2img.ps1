[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputImage,
    [Parameter(Mandatory = $true)]
    [string]$Prompt,
    [string]$NegativePrompt = 'lowres, bad anatomy, bad hands, extra limbs, distorted face, blurry, watermark, text, jpeg artifacts',
    [ValidateRange(0.0, 1.0)]
    [double]$Denoise = 0.55,
    [int]$Seed = 24681357,
    [int]$Steps = 8,
    [double]$Cfg = 1.0,
    [ValidateRange(0.01, 16.0)]
    [double]$Megapixels = 0.25,
    [string]$OutputPrefix = 'qwen21_img2img',
    [ValidateSet('auto', 'gpu', 'cpu', 'off')]
    [string]$CacheDevice = 'auto',
    [ValidateSet('default', 'int8', 'int4')]
    [string]$CacheDtype = 'default',
    [int]$Port = 8188
)

$ErrorActionPreference = 'Stop'
$baseUrl = "http://127.0.0.1:$Port"
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$app = Join-Path $projectRoot 'ComfyUI'
$python = Join-Path $app '.venv\Scripts\python.exe'
$source = Get-Item -LiteralPath $InputImage

if (-not $source.Exists) {
    throw "Input image not found: $InputImage"
}
$allowedExtensions = @('.png', '.jpg', '.jpeg', '.webp', '.bmp')
if ($source.Extension.ToLowerInvariant() -notin $allowedExtensions) {
    throw "Unsupported image type: $($source.Extension)"
}

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

Add-Type -AssemblyName System.Net.Http
$client = [System.Net.Http.HttpClient]::new()
$multipart = [System.Net.Http.MultipartFormDataContent]::new()
$stream = [System.IO.File]::OpenRead($source.FullName)
try {
    $fileContent = [System.Net.Http.StreamContent]::new($stream)
    $mime = switch ($source.Extension.ToLowerInvariant()) {
        '.png' { 'image/png' }
        '.webp' { 'image/webp' }
        '.bmp' { 'image/bmp' }
        default { 'image/jpeg' }
    }
    $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse($mime)
    $multipart.Add($fileContent, 'image', $source.Name)
    $uploadResponse = $client.PostAsync("$baseUrl/upload/image", $multipart).GetAwaiter().GetResult()
    $uploadBody = $uploadResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    if (-not $uploadResponse.IsSuccessStatusCode) {
        throw "Image upload failed ($([int]$uploadResponse.StatusCode)): $uploadBody"
    }
    $uploaded = $uploadBody | ConvertFrom-Json
    $inputName = if ($uploaded.name) { $uploaded.name } else { $uploaded.filename }
}
finally {
    $stream.Dispose()
    $multipart.Dispose()
    $client.Dispose()
}

if (-not $inputName) {
    throw "ComfyUI did not return an uploaded image name."
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
            device = $CacheDevice
            dtype = $CacheDtype
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
        class_type = 'LoadImage'
        inputs = @{ image = $inputName }
    }
    '7' = @{
        class_type = 'ImageScaleToTotalPixels'
        inputs = @{
            image = @('6', 0)
            upscale_method = 'area'
            megapixels = $Megapixels
            resolution_steps = 32
        }
    }
    '8' = @{
        class_type = 'VAEEncode'
        inputs = @{
            pixels = @('7', 0)
            vae = @('3', 0)
        }
    }
    '9' = @{
        class_type = 'KSampler'
        inputs = @{
            model = @('4', 0)
            positive = @('5', 0)
            negative = @('5', 1)
            latent_image = @('8', 0)
            seed = $Seed
            steps = $Steps
            cfg = $Cfg
            sampler_name = 'euler'
            scheduler = 'simple'
            denoise = $Denoise
        }
    }
    '10' = @{
        class_type = 'VAEDecode'
        inputs = @{
            samples = @('9', 0)
            vae = @('3', 0)
        }
    }
    '11' = @{
        class_type = 'SaveImage'
        inputs = @{
            images = @('10', 0)
            filename_prefix = $OutputPrefix
        }
    }
}

$body = @{
    prompt = $promptGraph
    client_id = 'codex-qwen21-img2img'
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
Write-Host "Queued Qwen-Image 2.1 img2img job: $promptId"
Write-Host "Input: $($source.FullName)"
Write-Host "Denoise: $Denoise | Steps: $Steps | CFG: $Cfg | Megapixels: $Megapixels"

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

$images = $entry.outputs.'11'.images
foreach ($image in $images) {
    $path = Join-Path (Join-Path $app 'output') $image.filename
    Write-Output $path
}
