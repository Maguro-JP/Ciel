#!/usr/bin/env python3
"""settings.json に登録された全フックを、無害な入力で1回ずつ動かす。

フックは全リポジトリに配られ、毎ターン・毎セッション動く。1本が壊れると、全部のセッションが
止まるか、毎ターン誤った差し戻しを受ける。配る前にここで捕まえる。
無害な入力（普通の依頼、根拠のある返答、マーカー無し）で exit 0 以外か、Traceback が出たら誤り。

使い方: python3 scripts/hooks-smoke.py [--root <リポジトリ>] [settings.json のパス]（既定は .claude/settings.json）
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def inputs(tmp: Path):
    t = tmp / "transcript.jsonl"
    rows = [
        {"type": "user", "message": {"content": "README を読んで"}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "./scripts/validate.sh"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "誤り 0  注意 0\nexit=0"}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "★ 済み: README.md:1 を読み、`scripts/validate.sh` が通りました。\n❕ 疑い: 他の検査は動かしていない。"}]}},
    ]
    t.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    base = {"session_id": "smoke", "transcript_path": str(t), "cwd": str(ROOT)}
    return {
        "SessionStart": [dict(base, hook_event_name="SessionStart", source="startup")],
        "UserPromptSubmit": [dict(base, hook_event_name="UserPromptSubmit", prompt="README を読んで"),
                             dict(base, hook_event_name="UserPromptSubmit", prompt="違う。言った通りに直して")],
        "PostToolUse": [dict(base, hook_event_name="PostToolUse", tool_name="Read",
                             tool_input={"file_path": str(ROOT / "README.md")}, tool_response={"ok": True})],
        "Stop": [dict(base, hook_event_name="Stop", stop_hook_active=False)],
        "PreToolUse": [dict(base, hook_event_name="PreToolUse", tool_name="Read", tool_input={"file_path": str(ROOT / "README.md")})],
    }


# フックの登録の先頭。どちらかで始まらない登録は、作業ディレクトリに頼っている
ANCHORS = ('"${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/run.sh" ', 'cd "${CLAUDE_PROJECT_DIR:-.}" && ')


def main() -> int:
    global ROOT
    args = [a for a in sys.argv[1:]]
    if "--root" in args:  # 別のリポジトリ（配布先）のフックを、そのリポジトリを作業場所にして動かす
        i = args.index("--root"); ROOT = Path(args[i + 1]).resolve(); del args[i:i + 2]
    settings = Path(args[0]) if args else ROOT / ".claude" / "settings.json"
    hooks = json.loads(settings.read_text(encoding="utf-8")).get("hooks", {})
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        env = dict(os.environ, HOME=d, DONE_CHECK_STATE=d, FOLLOW_INSTRUCTIONS_STATE=d)
        samples = inputs(tmp)
        for event, groups in hooks.items():
            for g in groups:
                for h in g.get("hooks", []):
                    cmd = h.get("command")
                    if not cmd:
                        continue
                    if not cmd.startswith(ANCHORS):
                        # 相対パスのままの登録は、会話の途中で cd すると見つからず、終了コード 2 で全部のツールを止める
                        bad += 1
                        print(f"  NG  {event:17} {cmd}  起動役（.claude/hooks/run.sh）を通していない")
                        continue
                    # ひな形には、対象のリポジトリで repo-bootstrap が作るフック（test.sh、check.sh）も登録されている。
                    # ここに無いファイルを指す登録は、動かさずに飛ばす（skill-sync の _command_exists と同じ見方）
                    paths = [t for t in cmd.replace("||", " ").split() if t.startswith(".claude/")]
                    if paths and not all((ROOT / t).exists() for t in paths):
                        print(f"  skip {event:17} {cmd}（このリポジトリに無い。対象で作られる）")
                        continue
                    for payload in samples.get(event, [{"session_id": "smoke"}]):
                        try:
                            r = subprocess.run(cmd, shell=True, cwd=ROOT, input=json.dumps(payload, ensure_ascii=False),  # code-check: ignore 固定の文字列（ユーザーの入力は入らない）
                                               capture_output=True, text=True, env=env, timeout=h.get("timeout", 30))
                            code, err = r.returncode, r.stderr
                        except subprocess.TimeoutExpired:
                            code, err = "timeout", ""
                        ok = code == 0 and "Traceback" not in err
                        mark = "ok  " if ok else "NG  "
                        if not ok:
                            bad += 1
                        detail = "" if ok else f"  exit={code} {err.strip().splitlines()[-1][:120] if err.strip() else ''}"
                        print(f"  {mark}{event:17} {cmd}{detail}")
                    # 別の作業ディレクトリ（cd したあと）からも 1 回動かし、見つからずに止まらないことを見る
                    try:
                        r = subprocess.run(cmd, shell=True, cwd=d, input=json.dumps(samples.get(event, [{"session_id": "smoke"}])[0], ensure_ascii=False),  # code-check: ignore 固定の文字列（ユーザーの入力は入らない）
                                           capture_output=True, text=True, env=dict(env, CLAUDE_PROJECT_DIR=str(ROOT)), timeout=h.get("timeout", 30))
                        code, err = r.returncode, r.stderr
                    except subprocess.TimeoutExpired:
                        code, err = "timeout", ""
                    if code != 0 or "Traceback" in err or "No such file" in err:
                        bad += 1
                        print(f"  NG  {event:17} {cmd}  別の作業ディレクトリから動かすと失敗する exit={code}")
    print(f"フックの誤り {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
