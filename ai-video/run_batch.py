#!/usr/bin/env python3
"""
run_batch.py - ComfyUI(로컬, --lowvram) 로 Image-to-Video 배치 렌더링

입력 폴더 규칙
  jobs/
    cat.png            <- 이미지 (png/jpg/jpeg/webp)
    cat.txt            <- 같은 이름의 모션 프롬프트 (없으면 --default-prompt 사용)
    cat.h3.txt         <- (선택) 모델별 프롬프트. --model h3 일 때 cat.txt 보다 우선
    prompts.csv        <- (선택) image,prompt[,negative,seconds,width,height,seed] 형식. txt 보다 우선

사용 예
  python run_batch.py --test                         # 샘플 이미지 자동 생성 후 1클립 테스트 + 리포트
  python run_batch.py jobs                           # 폴더 전체 렌더 -> jobs/_out/
  python run_batch.py jobs --res 720p --seconds 3
  python run_batch.py jobs --model h3 --seconds 3    # MiniMax H3 (고퀄, 오디오 포함, 느림)
  python run_batch.py jobs --workflow my_api.json    # 직접 저장한 API 워크플로우({{IMAGE}} 등 자리표시자)

사전 조건: start_comfyui.bat 으로 ComfyUI 가 127.0.0.1:8188 에서 실행 중.
결과: 각 MP4 + _out/report.json (소요 시간, 피크 VRAM/RAM, 남은 디스크)
"""
import argparse, csv, json, os, random, shutil, subprocess, sys, threading, time, uuid
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests psutil 필요")
try:
    import psutil
except ImportError:
    psutil = None

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
FPS = 24
DEFAULT_NEG = ("blurry, low quality, distorted, deformed, watermark, text, logo, "
               "static, jpeg artifacts, extra limbs")

# ------------------------------------------------------------------ 워크플로우
def wan22_ti2v_gguf(image_name, prompt, negative, width, height, frames, seed, steps, cfg, prefix):
    """Wan 2.2 TI2V-5B GGUF Q5_K_M - ComfyUI API 포맷 그래프."""
    return {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "Wan2.2-TI2V-5B-Q5_K_M.gguf"}},
        "2": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "wan2.2_vae.safetensors"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
        "7": {"class_type": "Wan22ImageToVideoLatent", "inputs": {
            "vae": ["3", 0], "width": width, "height": height, "length": frames,
            "batch_size": 1, "start_image": ["4", 0]}},
        "8": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0], "shift": 8.0}},
        "9": {"class_type": "KSampler", "inputs": {
            "model": ["8", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0],
            "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "uni_pc",
            "scheduler": "simple", "denoise": 1.0}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["3", 0]}},
        "11": {"class_type": "CreateVideo", "inputs": {"images": ["10", 0], "fps": float(FPS)}},
        "12": {"class_type": "SaveVideo", "inputs": {
            "video": ["11", 0], "filename_prefix": prefix, "format": "mp4", "format.codec": "h264"}},
    }


def minimax_h3_i2v(image_name, prompt, negative, width, height, frames, seed, steps, cfg, prefix,
                   lora="minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"):
    """MiniMax H3 FL2VA (pruned INT8 ConvRot + Qwen3-VL nvfp4) - ComfyUI 공식 i2v 템플릿을 API 포맷으로 옮김.
    negative/cfg 는 H3 템플릿(BasicGuider)에 없어서 쓰지 않음. lora=None 이면 Turbo LoRA 없이 steps 그대로."""
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "6": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {
            "clip": ["2", 0], "vae": ["3", 0], "first_frame": ["5", 0], "prompt": prompt,
            "width": width, "height": height, "length": frames}},
        "8": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "9": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "10": {"class_type": "BasicScheduler", "inputs": {
            "model": ["7", 0], "scheduler": "simple", "steps": steps, "denoise": 1.0}},
        "11": {"class_type": "BasicGuider", "inputs": {"model": ["7", 0], "conditioning": ["6", 0]}},
        "12": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["8", 0], "guider": ["11", 0], "sampler": ["9", 0], "sigmas": ["10", 0],
            "latent_image": ["6", 1]}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
        "14": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["12", 0], "vae": ["4", 0]}},
        "15": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "audio": ["14", 0], "fps": float(FPS)}},
        "16": {"class_type": "SaveVideo", "inputs": {
            "video": ["15", 0], "filename_prefix": prefix, "format": "mp4", "format.codec": "h264"}},
    }
    if lora:
        g["7"] = {"class_type": "LoraLoaderModelOnly", "inputs": {
            "model": ["1", 0], "lora_name": lora, "strength_model": 1.0}}
    else:
        g["7"] = g["1"]; del g["1"]
    return g


MODELS = {
    # name: (graph_fn, {res: (w,h)}, frame_rule, default_steps)
    "wan22": (wan22_ti2v_gguf, {"480p": (832, 480), "720p": (1280, 704)}, "4n+1", 20),
    "h3":    (minimax_h3_i2v, {"480p": (864, 480), "720p": (1280, 736)}, "17n+5", 8),
}


def snap_frames(seconds, rule):
    n = seconds * FPS
    if rule == "17n+5":  # H3: 위로 스냅 (공식 템플릿과 동일)
        return max(5, int(-(-(round(n) - 5) // 17)) * 17 + 5)
    return int(round(n / 4)) * 4 + 1


def custom_workflow(path, image_name, prompt, negative, width, height, frames, seed, steps, cfg, prefix):
    """외부 API 워크플로우(JSON) 의 자리표시자 {{IMAGE}} {{PROMPT}} ... 를 치환."""
    text = Path(path).read_text(encoding="utf-8")
    rep = {"IMAGE": image_name, "PROMPT": prompt, "NEGATIVE": negative, "PREFIX": prefix}
    for k, v in rep.items():
        text = text.replace("{{%s}}" % k, json.dumps(v)[1:-1])
    for k, v in {"WIDTH": width, "HEIGHT": height, "FRAMES": frames, "SEED": seed,
                 "STEPS": steps, "CFG": cfg, "FPS": FPS}.items():
        text = text.replace('"{{%s}}"' % k, str(v))
    return json.loads(text)

# ------------------------------------------------------------------ 모니터링
class Monitor(threading.Thread):
    """nvidia-smi / psutil 로 피크 VRAM, 시스템 RAM 측정."""
    def __init__(self, interval=0.5):
        super().__init__(daemon=True)
        self.interval, self.stop_flag = interval, False
        self.peak_vram_mb = 0
        self.peak_ram_gb = 0.0
        self.base_ram_gb = psutil.virtual_memory().used / 2**30 if psutil else 0.0

    def run(self):
        while not self.stop_flag:
            try:
                out = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5).stdout.strip().splitlines()
                if out:
                    self.peak_vram_mb = max(self.peak_vram_mb, int(out[0]))
            except Exception:
                pass
            if psutil:
                self.peak_ram_gb = max(self.peak_ram_gb, psutil.virtual_memory().used / 2**30)
            time.sleep(self.interval)

    def stop(self):
        self.stop_flag = True

# ------------------------------------------------------------------ ComfyUI API
class Comfy:
    def __init__(self, host):
        self.base = f"http://{host}"
        self.client_id = str(uuid.uuid4())

    def alive(self):
        try:
            return requests.get(f"{self.base}/system_stats", timeout=5).json()
        except Exception:
            return None

    def upload(self, path):
        with open(path, "rb") as f:
            r = requests.post(f"{self.base}/upload/image",
                              files={"image": (path.name, f)}, data={"overwrite": "true"}, timeout=60)
        r.raise_for_status()
        j = r.json()
        return f"{j['subfolder']}/{j['name']}" if j.get("subfolder") else j["name"]

    def queue(self, graph):
        r = requests.post(f"{self.base}/prompt", json={"prompt": graph, "client_id": self.client_id}, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"ComfyUI 그래프 오류: {r.text[:2000]}")
        return r.json()["prompt_id"]

    def wait(self, pid, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            h = requests.get(f"{self.base}/history/{pid}", timeout=30).json()
            if pid in h:
                st = h[pid].get("status", {})
                if st.get("status_str") == "error":
                    raise RuntimeError(json.dumps(st.get("messages", []), ensure_ascii=False)[:2000])
                return h[pid]
            time.sleep(2)
        raise TimeoutError(f"{timeout}s 초과")

    def fetch_outputs(self, hist, dest_dir):
        saved = []
        for node in hist.get("outputs", {}).values():
            for key in ("images", "videos", "gifs", "files"):
                for it in node.get(key, []):
                    fn = it.get("filename", "")
                    if not fn.lower().endswith((".mp4", ".webm", ".mov")):
                        continue
                    r = requests.get(f"{self.base}/view", params={
                        "filename": fn, "subfolder": it.get("subfolder", ""), "type": it.get("type", "output")},
                        timeout=300)
                    r.raise_for_status()
                    out = dest_dir / fn
                    out.write_bytes(r.content)
                    saved.append(out)
        return saved

# ------------------------------------------------------------------ 작업 수집
def collect_jobs(folder, default_prompt, model=None):
    folder = Path(folder)
    jobs = []
    csv_path = folder / "prompts.csv"
    if csv_path.exists():
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                img = folder / row["image"].strip()
                if img.exists():
                    jobs.append({"image": img, **{k: (v or "").strip() for k, v in row.items() if k != "image"}})
                else:
                    print(f"[건너뜀] 이미지 없음: {img}")
        return jobs
    for img in sorted(folder.iterdir()):
        if img.suffix.lower() in IMG_EXT:
            txt = img.with_suffix(f".{model}.txt") if model else None   # 모델별 프롬프트 우선 (예: cat.h3.txt)
            if not (txt and txt.exists()):
                txt = img.with_suffix(".txt")
            prompt = txt.read_text(encoding="utf-8").strip() if txt.exists() else default_prompt
            jobs.append({"image": img, "prompt": prompt})
    return jobs


def make_sample(folder):
    """저작권 없는 테스트 이미지를 절차적으로 생성 (해질녘 하늘 + 산 + 호수)."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 1280, 704
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(40 + 200 * t), int(60 + 90 * t), int(140 - 60 * t)))
    d.ellipse([820, 230, 960, 370], fill=(255, 210, 140))
    d.polygon([(0, 480), (250, 260), (480, 470), (700, 300), (980, 480), (1280, 330), (1280, 704), (0, 704)],
              fill=(40, 45, 70))
    d.rectangle([0, 520, w, h], fill=(70, 90, 140))
    for i in range(30):
        y = 530 + i * 6
        d.line([(860 - i * 3, y), (920 + i * 3, y)], fill=(230, 180, 130), width=2)
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    folder.mkdir(parents=True, exist_ok=True)
    im.save(folder / "sample_sunset.png")
    (folder / "sample_sunset.txt").write_text(
        "slow cinematic dolly-in toward a calm mountain lake at sunset, gentle ripples on the water, "
        "soft clouds drifting, warm light shimmering, smooth camera motion", encoding="utf-8")

# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description="ComfyUI I2V 배치 렌더러 (Wan 2.2 TI2V-5B GGUF 기본)")
    ap.add_argument("folder", nargs="?", help="이미지+프롬프트 폴더")
    ap.add_argument("--test", action="store_true", help="샘플 이미지로 1클립 테스트")
    ap.add_argument("--model", choices=MODELS, default="wan22", help="wan22(빠름) / h3(고퀄, 느림)")
    ap.add_argument("--res", choices=["480p", "720p"], default="480p")
    ap.add_argument("--landscape", action="store_true", help="세로 이미지도 가로 해상도로 강제")
    ap.add_argument("--seconds", type=float, default=2.5, help="클립 길이(초) - 24fps, 4n+1 프레임으로 맞춤")
    ap.add_argument("--steps", type=int, default=0, help="0 = 모델 기본값 (wan22 20, h3 Turbo 8)")
    ap.add_argument("--no-turbo", action="store_true", help="h3: Turbo LoRA 끄기 (steps 20 권장, 매우 느림)")
    ap.add_argument("--cfg", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=-1, help="-1 = 랜덤")
    ap.add_argument("--workflow", help="커스텀 API 워크플로우 JSON ({{IMAGE}} 등 자리표시자)")
    ap.add_argument("--default-prompt", default="subtle natural motion, cinematic, smooth camera movement")
    ap.add_argument("--host", default="127.0.0.1:8188")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--out", help="출력 폴더 (기본: <folder>/_out)")
    a = ap.parse_args()

    if a.test:
        folder = Path(__file__).resolve().parent / "test_input"
        make_sample(folder)
    elif a.folder:
        folder = Path(a.folder)
    else:
        ap.error("folder 또는 --test 필요")

    comfy = Comfy(a.host)
    stats = comfy.alive()
    if not stats:
        sys.exit(f"ComfyUI 응답 없음 ({a.host}). start_comfyui.bat 먼저 실행하세요.")
    dev = stats.get("devices", [{}])[0]
    print(f"ComfyUI OK - {dev.get('name', '?')}  VRAM {dev.get('vram_total', 0) / 2**30:.1f} GB")

    out_dir = Path(a.out) if a.out else folder / "_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = collect_jobs(folder, a.default_prompt, a.model)
    if not jobs:
        sys.exit("처리할 이미지가 없습니다.")
    print(f"{len(jobs)}개 작업")

    graph_fn, res_map, rule, def_steps = MODELS[a.model]
    steps = a.steps or (20 if (a.model == "h3" and a.no_turbo) else def_steps)
    results = []
    for i, job in enumerate(jobs, 1):
        w, h = res_map[a.res]
        if not a.landscape:
            try:  # 세로 사진(쇼츠 9:16)이면 해상도도 세로로
                from PIL import Image
                with Image.open(job["image"]) as im:
                    if im.height > im.width:
                        w, h = h, w
            except Exception:
                pass
        if job.get("width") and job.get("height"):
            w, h = int(job["width"]), int(job["height"])
        secs = float(job.get("seconds") or a.seconds)
        frames = snap_frames(secs, rule)
        seed = int(job.get("seed") or (a.seed if a.seed >= 0 else random.randint(0, 2**31 - 1)))
        prompt = job.get("prompt") or a.default_prompt
        neg = job.get("negative") or DEFAULT_NEG
        stem = job["image"].stem
        prefix = f"batch/{stem}_{int(time.time())}"
        print(f"\n[{i}/{len(jobs)}] {job['image'].name}  {w}x{h}  {frames}f ({frames / FPS:.2f}s)  seed={seed}")

        mon = Monitor(); mon.start()
        t0 = time.time()
        rec = {"image": job["image"].name, "prompt": prompt, "width": w, "height": h,
               "frames": frames, "fps": FPS, "seed": seed}
        try:
            name = comfy.upload(job["image"])
            args = (name, prompt, neg, w, h, frames, seed, steps, a.cfg, prefix)
            if a.workflow:
                graph = custom_workflow(a.workflow, *args)
            elif a.model == "h3":
                graph = minimax_h3_i2v(*args, lora=None if a.no_turbo else
                                       "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors")
            else:
                graph = graph_fn(*args)
            hist = comfy.wait(comfy.queue(graph), a.timeout)
            files = comfy.fetch_outputs(hist, out_dir)
            final = []
            for f in files:
                dst = out_dir / f"{stem}.mp4"
                if dst.exists():
                    dst = out_dir / f"{stem}_{seed}.mp4"
                shutil.move(f, dst)
                final.append(str(dst))
            rec.update(status="ok", outputs=final)
        except Exception as e:
            rec.update(status="error", error=str(e))
            print(f"  [오류] {e}")
        finally:
            mon.stop(); mon.join(timeout=2)
        rec.update(seconds_elapsed=round(time.time() - t0, 1),
                   peak_vram_gb=round(mon.peak_vram_mb / 1024, 2),
                   peak_ram_gb=round(mon.peak_ram_gb, 2))
        print(f"  {rec['status']}  {rec['seconds_elapsed']}s  피크 VRAM {rec['peak_vram_gb']}GB  "
              f"피크 RAM {rec['peak_ram_gb']}GB  {rec.get('outputs', '')}")
        results.append(rec)

    drive = Path(out_dir).resolve().anchor or "/"
    free_gb = round(shutil.disk_usage(drive).free / 2**30, 1)
    report = {"device": dev.get("name"), "model": a.model, "res": a.res, "steps": steps, "cfg": a.cfg,
              "workflow": a.workflow or a.model,
              "disk_free_gb": free_gb, "jobs": results}
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(r["status"] == "ok" for r in results)
    print(f"\n완료 {ok}/{len(results)}  |  남은 디스크 {free_gb} GB  |  리포트: {out_dir / 'report.json'}")


if __name__ == "__main__":
    main()
