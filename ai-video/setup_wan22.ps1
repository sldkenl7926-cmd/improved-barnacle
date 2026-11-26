# =====================================================================
#  setup_wan22.ps1  -  Windows 11 / RTX 5070 Laptop (sm_120) 용
#  ComfyUI + Wan 2.2 TI2V-5B (GGUF Q5_K_M) [+ MiniMax H3 INT8 ConvRot/nvfp4] 로컬 I2V 환경 설치
#
#  실행:  PowerShell (관리자 불필요)
#    Set-ExecutionPolicy -Scope Process Bypass
#    .\setup_wan22.ps1                 # Wan 2.2 만 (약 20GB)
#    .\setup_wan22.ps1 -WithH3         # + MiniMax H3 (추가 약 39GB)
#    .\setup_wan22.ps1 -Root D:\AI-Video
# =====================================================================
param(
    [string]$Root = "C:\AI-Video",
    [switch]$WithH3
)
$ErrorActionPreference = "Stop"
function Step($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Fail($m) { Write-Host "[실패] $m" -ForegroundColor Red; exit 1 }
function FreeGB { [math]::Round((Get-PSDrive ($Root.Substring(0,1))).Free / 1GB, 1) }

$log = @{}
$log.free_before_gb = FreeGB
$t0 = Get-Date

# ---------------------------------------------------------------- 1. 점검
Step "1단계: 사전 점검"
if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) { Fail "nvidia-smi 없음 - NVIDIA 드라이버(570 이상) 설치 필요" }
$gpu = nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
Write-Host "GPU: $gpu"
$drv = [double](($gpu -split ",")[1].Trim().Split(".")[0])
if ($drv -lt 570) { Fail "드라이버 $drv < 570. Blackwell(sm_120)은 570 이상 필요 - 드라이버 업데이트 후 재실행" }
# 현재 ComfyUI README: NVIDIA 는 PyTorch cu130 이상 요구 (cu130 은 드라이버 580 이상 필요)
if ($drv -ge 580) { $TorchIndex = "https://download.pytorch.org/whl/cu130" }
else {
    $TorchIndex = "https://download.pytorch.org/whl/cu128"
    Write-Host "경고: 드라이버 $drv -> cu128 로 설치. ComfyUI 권장(cu130)을 위해 580 이상으로 업데이트 권장" -ForegroundColor Yellow
}

foreach ($tool in @("git", "ffmpeg")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Host "$tool 없음 -> winget 설치 시도"
        $id = @{ git = "Git.Git"; ffmpeg = "Gyan.FFmpeg" }[$tool]
        winget install -e --id $id --accept-source-agreements --accept-package-agreements
        Write-Host "설치 후 새 PowerShell 창에서 이 스크립트를 다시 실행하세요." -ForegroundColor Yellow
        exit 0
    }
}
# Python 3.12 (3.13은 일부 커스텀 노드 휠 미지원 사례가 있어 3.12 권장)
$py = $null
try { $py = (& py -3.12 -c "import sys;print(sys.executable)") } catch {}
if (-not $py) {
    Write-Host "Python 3.12 없음 -> winget 설치"
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    Write-Host "설치 후 새 PowerShell 창에서 다시 실행하세요." -ForegroundColor Yellow
    exit 0
}
Write-Host "Python: $py"
$freeNow = FreeGB
Write-Host "여유 공간: $freeNow GB"
$need = 75; if ($WithH3) { $need = 115 }
if ($freeNow -lt $need) { Fail "여유 공간 $need GB 미만 - 설치 후 50GB 여유 확보 불가" }

# ---------------------------------------------------------------- 2. ComfyUI
Step "2단계: ComfyUI 설치 ($Root\ComfyUI)"
New-Item -ItemType Directory -Force -Path $Root | Out-Null
Set-Location $Root
if (-not (Test-Path "$Root\ComfyUI")) { git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git }
if (-not (Test-Path "$Root\venv")) { & py -3.12 -m venv "$Root\venv" }
$vpy = "$Root\venv\Scripts\python.exe"
& $vpy -m pip install --upgrade pip --no-cache-dir
# PyTorch: CUDA 12.8 빌드 (sm_120 지원). --no-cache-dir 로 pip 캐시 중복 저장 방지
& $vpy -m pip install --no-cache-dir torch torchvision torchaudio --index-url $TorchIndex
& $vpy -m pip install --no-cache-dir -r "$Root\ComfyUI\requirements.txt"

# GGUF 로더 커스텀 노드
$cn = "$Root\ComfyUI\custom_nodes"
if (-not (Test-Path "$cn\ComfyUI-GGUF")) { git clone --depth 1 https://github.com/city96/ComfyUI-GGUF.git "$cn\ComfyUI-GGUF" }
& $vpy -m pip install --no-cache-dir -r "$cn\ComfyUI-GGUF\requirements.txt"
& $vpy -m pip install --no-cache-dir psutil requests "huggingface_hub[hf_transfer]"

Step "sm_120 인식 확인"
$check = @'
import torch, sys
ok = torch.cuda.is_available()
print("torch", torch.__version__, "cuda", torch.version.cuda, "available", ok)
if not ok: sys.exit(2)
cap = torch.cuda.get_device_capability(0)
print("device", torch.cuda.get_device_name(0), "capability", cap, "arch_list", torch.cuda.get_arch_list())
if "sm_120" not in torch.cuda.get_arch_list(): sys.exit(3)
x = torch.randn(2048, 2048, device="cuda", dtype=torch.float16); (x @ x).sum().item()
print("CUDA matmul OK")
'@
$check | & $vpy -
if ($LASTEXITCODE -ne 0) { Fail "PyTorch가 RTX 5070(sm_120)을 인식하지 못함 (코드 $LASTEXITCODE). 드라이버/torch cu128 확인" }

# ---------------------------------------------------------------- 3. 모델
Step "3단계: Wan 2.2 TI2V-5B 모델 다운로드"
$m = "$Root\ComfyUI\models"
$files = @(
  @{ repo = "QuantStack/Wan2.2-TI2V-5B-GGUF";           file = "Wan2.2-TI2V-5B-Q5_K_M.gguf";                                dst = "$m\unet" },
  @{ repo = "Comfy-Org/Wan_2.1_ComfyUI_repackaged";     file = "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"; dst = "$m\text_encoders" },
  @{ repo = "Comfy-Org/Wan_2.2_ComfyUI_Repackaged";     file = "split_files/vae/wan2.2_vae.safetensors";                    dst = "$m\vae" }
)
if ($WithH3) {
    Step "3-2단계: MiniMax H3 (8GB 노트북용: pruned INT8 ConvRot + Qwen3-VL nvfp4 + Turbo 8step LoRA)"
    $files += @(
      @{ repo = "Comfy-Org/MiniMax-H3";      file = "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors"; dst = "$m\diffusion_models" },  # 19.53 GB
      @{ repo = "Comfy-Org/MiniMax-H3";      file = "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors";      dst = "$m\text_encoders" },     # 14.61 GB
      @{ repo = "Comfy-Org/MiniMax-H3";      file = "vae/minimax_h3_video_vae_int8_convrot.safetensors";               dst = "$m\vae" },               # 2.62 GB
      @{ repo = "Comfy-Org/MiniMax-H3";      file = "vae/minimax_h3_audio_vae_fp32.safetensors";                       dst = "$m\vae" },               # 0.58 GB
      @{ repo = "lightx2v/Minimax-h3-Turbo"; file = "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors";      dst = "$m\loras" }              # 1.82 GB
    )
}
$env:HF_HUB_ENABLE_HF_TRANSFER = "1"
foreach ($f in $files) {
    $name = Split-Path $f.file -Leaf
    if (Test-Path "$($f.dst)\$name") { Write-Host "이미 있음: $name"; continue }
    New-Item -ItemType Directory -Force -Path $f.dst | Out-Null
    $dl = @"
from huggingface_hub import hf_hub_download
import shutil, os
p = hf_hub_download(repo_id='$($f.repo)', filename='$($f.file)', local_dir=r'$Root\_dl')
shutil.move(p, os.path.join(r'$($f.dst)', os.path.basename(p)))
print('OK', os.path.basename(p))
"@
    $dl | & $vpy -
    if ($LASTEXITCODE -ne 0) { Fail "다운로드 실패: $($f.repo)/$($f.file) - 파일명이 변경됐다면 HF 페이지에서 확인 후 이 줄 수정" }
}
Remove-Item -Recurse -Force "$Root\_dl" -ErrorAction SilentlyContinue

# ---------------------------------------------------------------- 4. 런처
Step "4단계: 런처 생성"
# 기본 런처: 현재 ComfyUI 는 dynamic VRAM(자동 오프로딩)이 기본값이라 플래그 없이 8GB 에서 동작.
@"
@echo off
cd /d "$Root\ComfyUI"
"$vpy" main.py --listen 127.0.0.1 --port 8188 %*
"@ | Set-Content -Encoding ASCII "$Root\start_comfyui.bat"
# 요청하신 --lowvram 런처 (dynamic VRAM 이 켜져 있으면 --lowvram 은 효과 없음. OOM 시 --novram 시도)
@"
@echo off
cd /d "$Root\ComfyUI"
"$vpy" main.py --lowvram --listen 127.0.0.1 --port 8188 %*
"@ | Set-Content -Encoding ASCII "$Root\start_comfyui_lowvram.bat"

# ---------------------------------------------------------------- 5. 정리
Step "5단계: 캐시 정리"
& $vpy -m pip cache purge
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\pip\cache" -ErrorAction SilentlyContinue
# HF 캐시는 local_dir 로 받아서 거의 없음. 남아있다면 xet/blob 중복 제거
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\models--QuantStack--Wan2.2-TI2V-5B-GGUF" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\models--Comfy-Org--*" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\models--lightx2v--*" -ErrorAction SilentlyContinue

$log.free_after_gb = FreeGB
$log.minutes = [math]::Round(((Get-Date) - $t0).TotalMinutes, 1)
$log.used_gb = [math]::Round($log.free_before_gb - $log.free_after_gb, 1)
$log | ConvertTo-Json | Set-Content "$Root\setup_report.json"
Write-Host "`n설치 완료: 사용 $($log.used_gb) GB / 남은 공간 $($log.free_after_gb) GB / $($log.minutes) 분" -ForegroundColor Green
if ($log.free_after_gb -lt 50) { Write-Host "경고: 남은 공간 50GB 미만" -ForegroundColor Red }
Write-Host "다음:  $Root\start_comfyui.bat 실행 후 (다른 창에서)  $vpy run_batch.py --test"
