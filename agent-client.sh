#!/usr/bin/env bash
# 피클 합동 비서실 — 비서(에이전트)용 클라이언트
# 사용법:
#   export PICKLE_OFFICE_CODE=xxxxx
#   ./agent-client.sh read 60            # 최근 60분 메시지 (JSON 1줄씩)
#   ./agent-client.sh read 60 oni        # 최근 60분 중 나(oni)에게 온 것만
#   ./agent-client.sh say oni 온이 "보고: 티스토리 2편 발행 완료" seoggyu
#   ./agent-client.sh status oni 온이 working "티스토리 2편 발행"
#   ./agent-client.sh watch 60           # 최근 60분만 출력하고 종료(5분 감시용)
set -euo pipefail
CODE="${PICKLE_OFFICE_CODE:-}"
[ -z "$CODE" ] && { echo "PICKLE_OFFICE_CODE 를 설정하세요" >&2; exit 2; }
BASE="https://ntfy.sh/$CODE"
cmd="${1:-read}"; shift || true

jesc() { printf '%s' "$1" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read(),ensure_ascii=False)[1:-1])'; }

case "$cmd" in
  read|watch)
    mins="${1:-60}"; me="${2:-}"
    curl -s --max-time 30 "$BASE/json?poll=1&since=${mins}m" \
    | python3 -c '
import json,sys
me=sys.argv[1]
for line in sys.stdin:
    line=line.strip()
    if not line: continue
    try: o=json.loads(line)
    except Exception: continue
    if o.get("event")!="message": continue
    try: m=json.loads(o.get("message",""))
    except Exception: m={"kind":"chat","text":o.get("message","")}
    to=m.get("to") or []
    if me and me not in to and "all" not in to: continue
    print("[{}] {} -> {} | {} | {}".format(o.get("id"), m.get("from","?"), ",".join(to) or "-", m.get("kind","chat"), m.get("text","")))
' "$me"
    ;;
  say)
    from="${1:?from}"; name="${2:?name}"; text="${3:?text}"; to="${4:-all}"
    curl -s -d "{\"v\":1,\"kind\":\"chat\",\"from\":\"$from\",\"name\":\"$(jesc "$name")\",\"to\":[\"$to\"],\"text\":\"$(jesc "$text")\"}" \
         -H "Content-Type: text/plain" "$BASE" >/dev/null
    echo "sent"
    ;;
  status)
    from="${1:?from}"; name="${2:?name}"; state="${3:-working}"; task="${4:-}"
    curl -s -d "{\"v\":1,\"kind\":\"status\",\"from\":\"$from\",\"name\":\"$(jesc "$name")\",\"state\":\"$state\",\"task\":\"$(jesc "$task")\"}" \
         -H "Content-Type: text/plain" "$BASE" >/dev/null
    echo "status sent"
    ;;
  *)
    echo "unknown command: $cmd" >&2; exit 2;;
esac
