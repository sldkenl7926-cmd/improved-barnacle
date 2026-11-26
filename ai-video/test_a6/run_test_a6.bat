@echo off
REM A6_01.jpg (홍학) -> Wan 2.2 5B 2.5초 + MiniMax H3 5초
REM 사전: start_comfyui.bat 실행 중 / 구글 드라이브 '유튜브_새채널_사진_2026-11-26' 의 A6_01.jpg 를 C:\AI-Video\test_a6 에 저장
chcp 65001 >nul
set PY=C:\AI-Video\venv\Scripts\python.exe
set DIR=C:\AI-Video\test_a6
set HERE=%~dp0
if not exist "%DIR%" mkdir "%DIR%"
copy /Y "%HERE%A6_01.txt" "%DIR%\" >nul
copy /Y "%HERE%A6_01.h3.txt" "%DIR%\" >nul
if not exist "%DIR%\A6_01.jpg" if exist "%HERE%A6_01.jpg" copy /Y "%HERE%A6_01.jpg" "%DIR%\" >nul
if not exist "%DIR%\A6_01.jpg" (echo [중단] %DIR%\A6_01.jpg 가 없습니다. 드라이브에서 받아 넣어 주세요. & exit /b 1)

echo ==== 1) Wan 2.2 TI2V-5B  480x832  2.5초 ====
"%PY%" "%HERE%..\run_batch.py" "%DIR%" --model wan22 --seconds 2.5 --seed 2026 --out "%DIR%\_out_wan22"
echo ==== 2) MiniMax H3  480x864  5초 (Turbo 8step, 오디오 포함) ====
"%PY%" "%HERE%..\run_batch.py" "%DIR%" --model h3 --seconds 5 --seed 2026 --out "%DIR%\_out_h3"

echo.
echo 결과: %DIR%\_out_wan22\A6_01.mp4  /  %DIR%\_out_h3\A6_01.mp4
echo 소요 시간: 각 폴더의 report.json  (seconds_elapsed)
