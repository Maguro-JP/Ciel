#!/usr/bin/env python3
"""settings.json に登録されたフックを見本の入力で動かし、1 ターンに差し込む文字数を測る。

毎ターン同じ決まりを差し込むと、それ自体がトークンの無駄になる。目安は 1 ターンの合計 1,200 文字、
SessionStart の合計 5,000 文字。超えたら、出す頻度を落とすか、短くする。

測るイベントは 4 つ。
  SessionStart、UserPromptSubmit  無害な入力で 2 回動かし、2 回目（普段のターン）の長さを見る
  PostToolUse、Stop               知らせと差し戻しが出る見本（悪い出力、悪いコード、根拠の無い返答）で 1 回動かす。
                                  無害な入力では何も出ないので、長さを測れない。見本ごとに合計を出し、どれも 1 ターンの目安と比べる
数えるのは、Claude の文脈に入る文だけ（delivered）。JSON の additionalContext、止めるフックの reason と標準エラー、
SessionStart と UserPromptSubmit の素の標準出力。端末に出るだけの systemMessage と、届かない素の標準出力は数えない。
測定の実行は、本物の置き場（~/.claude/state/）に書かない（clean_env）。

使い方: measure_hooks.py [settings.json] [--budget 1200] [--start-budget 5000]
目安を超えると exit 1。
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


STATE = tempfile.mkdtemp()
PROMPT = "README の表を直して"
# 悪い見本。このファイル自身が検査に当たらないように、分けて書く
SAME3 = "".join(f"repo-{c}: precheck 落ちた（test_sync.py FAILED failures=1）\n" for c in "abc") + "誤り 0  注意 0\n"
CRASH = 'Traceback (most recent call last):\n  File "app.py", line 3, in <module>\n    main()\nRuntime' + "Error: 起動できない\n"
BAD_CODE = ("import requests_html\nimport subprocess\n\n\ndef load(path):\n    try:\n        return open(path).read()\n"
            "    except Exception:\n        pa" + "ss\n\n\ndef run(cmd):\n    return subprocess.run(cmd, sh" + "ell=True)\n\n\nrun(load('x'))\n")
BAD_REPLY = "直しました。テストも通りました。たぶん動くはずです。"


def clean_env(home: str = "") -> dict:
    """フックに渡す環境。測定の実行が、本物の置き場（~/.claude/state/ の状態と metrics.jsonl）に書かないようにする。
    置き場の環境変数を 1 つずつ渡す形は、フックが増えるたびに漏れた（測定の行が、週 1 回の数に混ざった）。
    HOME を一時の場所に向け、呼んだ側の *_STATE は渡さない（渡すと、そこに書く）。git の設定だけは、元の場所を指す。"""
    env = {k: v for k, v in os.environ.items() if not k.endswith("_STATE")}
    gitconfig = Path.home() / ".gitconfig"
    if gitconfig.is_file() and "GIT_CONFIG_GLOBAL" not in env:
        env["GIT_CONFIG_GLOBAL"] = str(gitconfig)
    env["HOME"] = home or STATE
    return env


def delivered(event: str, code: int, stdout: str, stderr: str) -> str:
    """フックの出力のうち、Claude の文脈に入る文。"""
    if code == 2:
        return stderr.strip()  # 止めるフック。標準エラーが Claude に戻る
    if code != 0:
        return ""  # 落ちたフックの文は届かない
    try:
        d = json.loads(stdout) if stdout.lstrip().startswith("{") else None
    except ValueError:
        d = None
    if isinstance(d, dict):
        parts = []
        hso = d.get("hookSpecificOutput")
        if isinstance(hso, dict) and hso.get("additionalContext"):
            parts.append(str(hso["additionalContext"]))
        if d.get("decision") == "block" and d.get("reason"):
            parts.append(str(d["reason"]))
        return "\n".join(parts)  # systemMessage は端末に出るだけ
    return stdout if event in ("SessionStart", "UserPromptSubmit") else ""  # 素の標準出力が届くのは、開始と入力のときだけ


def matches(matcher, tool: str) -> bool:
    """登録の matcher が、そのツールに当たるか。空と * は全部に当たる。"""
    if not matcher or matcher == "*":
        return True
    try:
        return re.fullmatch(matcher, tool) is not None
    except re.error:
        return matcher == tool


def run(cmd: str, payload: dict, event: str, times: int = 2, home: str = "") -> int:
    """times 回動かして、最後の回に文脈へ入る長さを返す。1 ターン目だけ全文を出すフックがあるので、開始と入力は 2 回目（普段のターン）を測る。"""
    n = 0
    for _ in range(times):
        try:
            r = subprocess.run(cmd, shell=True, input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True, timeout=60,  # code-check: ignore 固定の文字列（ユーザーの入力は入らない）
                               env=clean_env(home))
            n = len(delivered(event, r.returncode, r.stdout, r.stderr))
        except (OSError, subprocess.TimeoutExpired):
            return 0
    return n


def label(cmd: str) -> str:
    """登録のコマンドから、起動役の部分を除いた名前。"""
    return cmd.split('run.sh" ')[-1][:72]


def transcript(tmp: Path, name: str, rows: list) -> str:
    p = tmp / f"{name}.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return str(p)


def user(text: str) -> dict:
    return {"type": "user", "origin": {"kind": "human"}, "message": {"role": "user", "content": text}}


def samples(tmp: Path) -> dict:
    """PostToolUse と Stop の見本 {イベント: [(名前, 入力)]}。知らせと差し戻しが出る形にする。"""
    bad = tmp / "app" / "main.py"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(BAD_CODE, encoding="utf-8")
    try:
        # 書いたファイルを見るフックは、リポジトリの中のファイルだけを見る。見本の置き場を、一時のリポジトリにする
        subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        pass  # git が無ければ、リポジトリの中だけを見るフックの分は 0 と出る
    plain = transcript(tmp, "plain", [user(PROMPT)])

    def bash(command: str, stdout: str) -> dict:
        return {"tool_name": "Bash", "tool_input": {"command": command}, "transcript_path": plain,
                "tool_response": {"stdout": stdout, "stderr": "", "interrupted": False, "isImage": False}}

    write = {"tool_name": "Write", "tool_input": {"file_path": str(bad), "content": BAD_CODE}, "transcript_path": plain,
             "tool_response": {"type": "create", "filePath": str(bad), "content": BAD_CODE, "structuredPatch": [], "originalFile": None}}
    edit = {"type": "tool_use", "id": "w1", "name": "Write", "input": {"file_path": str(bad), "content": BAD_CODE}}
    ended = transcript(tmp, "ended", [
        user("app/main.py を直して"),
        {"type": "assistant", "message": {"role": "assistant", "content": [edit]}},
        {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "w1", "content": "File created successfully"}]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": BAD_REPLY}]}}])
    return {
        "PostToolUse": [("Bash: 同じ失敗が並ぶ出力", bash("python3 sync_all.py", SAME3)),
                        ("Bash: クラッシュの出力", bash("python3 app.py", CRASH)),
                        ("Bash: push のあと", bash("git push origin HEAD", "To https://example.invalid/o/r.git\n   1111111..2222222  HEAD -> work\n")),
                        ("Write: 握りつぶしと外の依存のあるコード", write)],
        "Stop": [("根拠の無い完了と推測の語で終える返答", {"transcript_path": ended, "stop_hook_active": False, "last_assistant_message": BAD_REPLY})],
    }


def main() -> int:
    args = sys.argv[1:]
    budget = int(args[args.index("--budget") + 1]) if "--budget" in args else 1200
    start_budget = int(args[args.index("--start-budget") + 1]) if "--start-budget" in args else 5000
    settings = next((a for a in args if a.endswith(".json")), ".claude/settings.json")
    d = json.load(open(settings, encoding="utf-8"))
    hooks = d.get("hooks", {})
    work = Path(tempfile.mkdtemp())
    plain = transcript(work, "start", [{"type": "user", "message": {"content": PROMPT}}])
    sid = "measure-" + Path(STATE).name
    over = False
    for ev, limit in (("SessionStart", start_budget), ("UserPromptSubmit", budget)):
        total = 0
        for row in hooks.get(ev, []):
            for h in row.get("hooks", []):
                payload = {"session_id": sid, "transcript_path": plain, "cwd": os.getcwd(), "hook_event_name": ev, "prompt": PROMPT, "source": "startup"}
                n = run(h["command"], payload, ev)
                total += n
                print(f"  {ev:17} {n:6d}  {label(h['command'])}")
        mark = "超過" if total > limit else "目安内"
        over = over or total > limit
        print(f"{ev} 合計 {total} 文字（目安 {limit}）: {mark}")
    for ev, cases in samples(work).items():
        if not hooks.get(ev):
            continue
        for i, (name, sample) in enumerate(cases):
            total = 0
            home = tempfile.mkdtemp()  # 見本ごとに新しい状態。「同じ知らせは 1 回だけ」のフックも、最初の 1 回を測る
            for row in hooks.get(ev, []):
                if ev == "PostToolUse" and not matches(row.get("matcher"), sample["tool_name"]):
                    continue
                for h in row.get("hooks", []):
                    payload = dict(sample, session_id=f"{sid}-{ev}-{i}", cwd=os.getcwd(), hook_event_name=ev)
                    n = run(h["command"], payload, ev, times=1, home=home)
                    total += n
                    print(f"  {ev:17} {n:6d}  {label(h['command'])}")
            mark = "超過" if total > budget else "目安内"
            over = over or total > budget
            print(f"{ev}（{name}） 合計 {total} 文字（目安 {budget}）: {mark}")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
