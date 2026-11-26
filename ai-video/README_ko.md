# 로컬 AI 영상(I2V) 파이프라인: HP OMEN 17 / RTX 5070 Laptop 8GB

## 1. 설치 (PowerShell, 일반 권한)

```powershell
cd <이 폴더>
Set-ExecutionPolicy -Scope Process Bypass
.\setup_wan22.ps1            # 1~2단계: 점검 + ComfyUI + Wan 2.2 5B (약 20GB)
.\setup_wan22.ps1 -WithH3    # 3단계까지: + MiniMax H3 (추가 약 39GB). 이미 받은 파일은 건너뜁니다
```

스크립트가 하는 일:
- 점검: 드라이버(570 미만이면 중단, 580 이상이면 cu130), Git, FFmpeg, Python 3.12, 여유 공간
- `C:\AI-Video\ComfyUI` + `C:\AI-Video\venv`에 설치. pip는 `--no-cache-dir`로 실행
- PyTorch가 `sm_120`을 지원하는지, RTX 5070에서 CUDA matmul이 실제로 도는지 확인하고 실패하면 중단
- 모델 다운로드 (Hugging Face → 각 models 하위 폴더)
- 마지막에 pip/HF 캐시를 지우고 `C:\AI-Video\setup_report.json`에 사용 용량, 남은 용량, 소요 시간을 기록

| 모델 | 파일 | 용량 |
|---|---|---|
| Wan 2.2 TI2V-5B | `unet/Wan2.2-TI2V-5B-Q5_K_M.gguf` | 3.8 GB |
| | `text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.27 GB |
| | `vae/wan2.2_vae.safetensors` | 1.31 GB |
| MiniMax H3 | `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 19.53 GB |
| | `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 14.61 GB |
| | `vae/minimax_h3_video_vae_int8_convrot.safetensors` | 2.62 GB |
| | `vae/minimax_h3_audio_vae_fp32.safetensors` | 0.58 GB |
| | `loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | 1.82 GB |

예상 총량은 ComfyUI+venv 약 8GB에 모델 약 51GB를 더한 **약 60GB**입니다. 188GB에서 시작하면 **약 125GB가 남습니다** (예상치이며, 실제 값은 setup_report.json에 기록됩니다).

## 2. 실행

```bat
C:\AI-Video\start_comfyui.bat            :: 권장 (dynamic VRAM 자동 오프로딩)
C:\AI-Video\start_comfyui_lowvram.bat    :: --lowvram 버전
```

다른 창에서:

```bat
C:\AI-Video\venv\Scripts\python.exe run_batch.py --test                          :: 4단계 테스트 클립 (Wan, 480p, 61f = 2.54초 @24fps)
C:\AI-Video\venv\Scripts\python.exe run_batch.py --test --model h3 --seconds 3   :: H3 테스트 (864x480, 73f = 3.04초, 오디오 포함)
```

`--test`는 코드로 그린 노을 호수 이미지(저작권 없음)를 만들어 렌더합니다. 결과는 `test_input\_out\sample_sunset.mp4`와 `report.json`(소요 시간, 피크 VRAM/RAM, 남은 디스크)입니다. 워터마크는 넣지 않습니다.

## 3. 배치 렌더링 (다음부터는 폴더만 넘기면 됨)

```
jobs\
  cat.png   + cat.txt      ← 같은 이름의 txt = 모션 프롬프트
  city.jpg  + city.txt
  (또는 prompts.csv: image,prompt,negative,seconds,width,height,seed)
```

```bat
python run_batch.py jobs                       :: Wan 2.2, 480p, 2.5초
python run_batch.py jobs --res 720p --seconds 3
python run_batch.py jobs --model h3            :: 고퀄 컷
```

결과는 `jobs\_out\<이미지이름>.mp4`와 `jobs\_out\report.json`에 저장됩니다.

## 4. 주의

- H3 학습 길이는 약 5~15초(124~362프레임)입니다. 2~3초는 학습 범위보다 짧아서 품질이 떨어질 수 있습니다. 고퀄 컷은 `--seconds 5`를 권장합니다.
- H3를 32GB RAM으로 돌리면 모델(19.5GB)과 텍스트 인코더(14.6GB)를 RAM/디스크로 번갈아 옮기면서 동작합니다. Windows 페이지 파일을 "시스템 관리"로 두고, C드라이브에 20GB 이상 여유를 유지하세요.
- 상업적 이용 조건은 출처마다 다르게 적혀 있습니다. MiniMax H3 Community License 원문을 확인하세요.
