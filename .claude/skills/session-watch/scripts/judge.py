#!/usr/bin/env python3
"""セッションの見張り。list_sessions と list_triggers の結果から、サボり・止まり・無駄を判定し、処置を並べる。

セッションは放っておくと溜まる。終わったのに残るもの、ルーティンは動くのに成果が増えないもの、落ちたまま止まるもの、
人の答え待ちで止まるもの。見るたびに人が読み分けるのは続かないので、機械で判定し、処置の一覧（消す・起こす・知らせる・聞く）を出す。
MCP の一覧は Python から呼べないので、セッションが `list_sessions` と `list_triggers` の結果を JSON のファイルに書き、ここに渡す。

使い方: judge.py --sessions sessions.json --triggers triggers.json [--clones /home/user] [--no-fetch] [--days 3] [--stale 30] [--json actions.json] [--now ISO]
  sessions.json: list_sessions の結果（{"ccr":{"data":[...]}} でも {"data":[...]} でも [...] でもよい）。複数ページは配列をつなげる
  triggers.json: list_triggers の結果（同じ形）。include_completed を付けたものでもよい
  --clones: リポジトリの clone の親。ルーティンのプロンプトの owner/repo から、成果（コミット）が増えているかを見る
出力: Markdown の表（標準出力）と、--json に処置の一覧 {"archive": [...], "fire": [...], "notify": [...], "ask": [...]}
"""

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

LIMIT = re.compile(r"weekly limit|rate limit|rejected|上限", re.I)
REPO = re.compile(r"\b([\w.-]+)/([\w.-]+)\b")
AI_TAGS = ("feedback-session:", "ciel:", "config:meta-mcp-own-entry")


def load(path: str):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(d, dict):
        d = d.get("ccr", d)
        d = d.get("data", d)
    return d if isinstance(d, list) else []


def when(s: str):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def ai_made(s: dict) -> bool:
    tags = s.get("tags") or []
    return bool(s.get("parent_session_id")) or s.get("origin") == "claude_code_mcp_seed" or any(t.startswith(AI_TAGS) or t in AI_TAGS for t in tags)


def repo_of(prompt: str):
    """ルーティンのプロンプトに出てくる最初の owner/repo。無ければ None。"""
    for m in REPO.finditer(prompt or ""):
        owner, name = m.group(1), m.group(2)
        if owner.lower() in ("claude", "docs", "scripts", "tests", "src", "app", ".claude", "home", "tmp") or name.endswith((".md", ".py", ".sh", ".json", ".yml")):
            continue
        if "/" in m.group(0) and not m.group(0).startswith("."):
            return name
    return None


def commits_since(clones: Path, repo: str, days: int, fetch: bool):
    """clone の中のデフォルトブランチで、days 日以内のコミット数。clone が無ければ None。"""
    if not clones or not repo:
        return None
    d = None
    for cand in clones.iterdir() if clones.exists() else []:
        if cand.name.lower() == repo.lower() and (cand / ".git").exists():
            d = cand
            break
    if d is None:
        return None
    ref = subprocess.run(["git", "-C", str(d), "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD"], capture_output=True, text=True).stdout.strip() or "origin/main"
    if fetch:
        subprocess.run(["git", "-C", str(d), "fetch", "-q", "origin", ref.split("/", 1)[1]], capture_output=True, text=True)
    r = subprocess.run(["git", "-C", str(d), "log", f"--since={days} days ago", "--oneline", ref], capture_output=True, text=True)
    return len([l for l in r.stdout.splitlines() if l.strip()]) if r.returncode == 0 else None


def judge(sessions, triggers, now, clones=None, days=3, stale=30, fetch=False):
    bound = {}
    for t in triggers:
        sid = t.get("persistent_session_id")
        if sid:
            bound.setdefault(sid, []).append(t)
    rows, actions = [], {"archive": [], "fire": [], "notify": [], "ask": []}
    for s in sessions:
        sid, title = s.get("id", ""), (s.get("title") or "")[:40]
        status, bucket = s.get("session_status", ""), s.get("status_bucket", "")
        if "ARCHIVED" in status:
            continue
        upd = when(s.get("updated_at") or "")
        idle = (now - upd).days if upd else 999
        summ = s.get("post_turn_summary") or {}
        detail = " ".join(str(summ.get(k, "")) for k in ("status_detail", "needs_action", "recent_action"))[:80]
        mine = bound.get(sid, [])
        enabled = [t for t in mine if t.get("enabled")]
        tags = s.get("tags") or []
        keep = "feedback-session:keep" in tags
        if "BLOCKED" in bucket or "REQUIRES_ACTION" in status:
            verdict, why, act = "答え待ち", f"{idle} 日。{detail}", "知らせる（答えはユーザー）"
            actions["notify"].append({"id": sid, "title": title, "why": detail})
        elif "FAILED" in bucket:
            if LIMIT.search(detail):
                verdict, why, act = "上限で止まった", detail, "待つ（戻ったら次の実行で動く）"
            elif enabled:
                verdict, why, act = "落ちた", detail, "起こす（1 回）"
                actions["fire"].append({"id": sid, "title": title, "trigger": enabled[0].get("id"), "why": detail})
            elif idle >= stale and not keep:
                verdict, why, act = "無駄の候補", f"落ちたまま {idle} 日、ルーティン無し", "聞く（消してよいか）"
                actions["ask"].append({"id": sid, "title": title, "why": why})
            else:
                verdict, why, act = "落ちた", detail, "知らせる（ルーティン無し）"
                actions["notify"].append({"id": sid, "title": title, "why": detail})
        elif "WORKING" in bucket or "RUNNING" in status:
            if idle >= 1:
                verdict, why, act = "動いたまま止まっている", f"{idle} 日 RUNNING", "知らせる"
                actions["notify"].append({"id": sid, "title": title, "why": why})
            else:
                verdict, why, act = "動いている", detail, "無し"
        elif enabled:
            repo = next((repo_of(t.get("derived_state", {}).get("prompt") or t.get("prompt") or "") for t in enabled), None)
            n = commits_since(clones, repo, days, fetch)
            last = (enabled[0].get("last_run") or {}).get("status", "")
            if n is None:
                verdict, why, act = "分からない", f"clone 無し（{repo}）", "知らせる"
                actions["notify"].append({"id": sid, "title": title, "why": why})
            elif n == 0 and "SUCCEEDED" in last:
                verdict, why, act = "サボり", f"ルーティンは動くが {days} 日間コミット 0（{repo}）。{detail}", "起こす（1 回）と知らせる"
                actions["fire"].append({"id": sid, "title": title, "trigger": enabled[0].get("id"), "why": why})
                actions["notify"].append({"id": sid, "title": title, "why": why})
            else:
                verdict, why, act = "回っている", f"{days} 日でコミット {n}", "無し"
        elif ai_made(s) and not keep and idle >= days:
            verdict, why, act = "無駄", f"AI が立てて {idle} 日、ルーティン無し", "消す（アーカイブ）"
            actions["archive"].append({"id": sid, "title": title, "why": why})
        elif not keep and idle >= stale:
            verdict, why, act = "無駄の候補", f"人が開いて {idle} 日、ルーティン無し", "聞く（消してよいか）"
            actions["ask"].append({"id": sid, "title": title, "why": why})
        else:
            verdict, why, act = "待機", f"{idle} 日", "無し"
        rows.append((title, status.replace("SESSION_STATUS_", ""), verdict, why, act))
    alive = {s.get("id") for s in sessions if "ARCHIVED" not in s.get("session_status", "")}
    for t in triggers:
        sid = t.get("persistent_session_id")
        if t.get("enabled") and sid and sid not in alive:
            why = "紐づけ先のセッションが消えている（アーカイブ済みか一覧に無い）"
            rows.append(((t.get("name") or "")[:40], "ルーティン", "宙に浮いたルーティン", why, "知らせる（ルーティンを無効にするか、セッションを戻すかはユーザー）"))
            actions["notify"].append({"id": t.get("id"), "title": t.get("name"), "why": why})
    order = {"サボり": 0, "宙に浮いたルーティン": 0, "落ちた": 1, "動いたまま止まっている": 2, "答え待ち": 3, "分からない": 4, "無駄": 5, "無駄の候補": 6, "上限で止まった": 7, "回っている": 8, "動いている": 9, "待機": 10}
    rows.sort(key=lambda r: order.get(r[2], 99))
    return rows, actions


def render(rows, actions, now) -> str:
    L = [f"# セッションの見張り {now.astimezone(dt.timezone(dt.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M')}（日本時間）", "",
         "| セッション | 状態 | 判定 | 根拠 | 処置 |", "|---|---|---|---|---|"]
    for r in rows:
        L.append("| " + " | ".join(str(x).replace("|", "／") for x in r) + " |")
    L += ["", f"処置: 消す {len(actions['archive'])}、起こす {len(actions['fire'])}、知らせる {len(actions['notify'])}、聞く {len(actions['ask'])}"]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--triggers", required=True)
    ap.add_argument("--clones")
    ap.add_argument("--no-fetch", action="store_true", help="clone を取り直さない（テスト用。取り直さないと古い clone で動いているものがサボりに見える）")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--stale", type=int, default=30)
    ap.add_argument("--json")
    ap.add_argument("--now")
    a = ap.parse_args()
    now = when(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    rows, actions = judge(load(a.sessions), load(a.triggers), now, Path(a.clones) if a.clones else None, a.days, a.stale, not a.no_fetch)
    print(render(rows, actions, now))
    if a.json:
        Path(a.json).write_text(json.dumps(actions, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
