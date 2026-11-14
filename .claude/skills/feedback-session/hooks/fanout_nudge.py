#!/usr/bin/env python3
"""UserPromptSubmit フック: 独立した指示が 2 つ以上あるときに、子のセッションに分ける計画（fanout.py plan）を促す。

分ける合図が人の言葉（「並列で」）待ちだと、子のセッションは使われず、1 本で順に進めて開発が遅いままになる。
指示の数と語から機械で合図を出す。差し込むのは 1 行で、同じセッションでは 15 分に 1 回。
親から分けられた子のセッション（プロンプトに「セッションやルーティンを作らない」がある）には出さない。

環境変数:
  FANOUT_OFF=1         止める
  FANOUT_NUDGE_MIN=N   同じセッションで次に出すまでの分数（既定 15）
  FANOUT_STATE_DIR     覚える場所（既定 ~/.claude/state/fanout）
"""

import json
import os
import re
import sys
import time
from pathlib import Path

WORDS = re.compile(r"並列|並行|同時に|それぞれ|手分け|(?:全部の|全|各|複数の)リポジトリ")
ITEM = re.compile(r"(?m)^\s*(?:\d+\s*[.)．、:：]|[①-⑳・]|[-*+]\s)\s*\S")
REQUEST = re.compile(r"(?:して|しろ|やれ|くれ|ください|ように|すること|する|直す|作る|改善|切り替える|入れる|足す|消す|せ|け|て|(?<!の)で)$")
SYSTEMISH = re.compile(r"<task-notification>|^\s*Stop hook feedback|<wake reason=")
CHILD = re.compile(r"セッションやルーティンを作らない|親のセッションから分けた 1 本")


def count_instructions(prompt: str) -> int:
    """独立した指示の数。番号や「・」の列があればその数、無ければ頼む形で終わる文の数。"""
    items = len(ITEM.findall(prompt))
    if items >= 2:
        return items
    sentences = [s.strip(" 　、") for s in re.split(r"[。\n！!]", prompt)]
    return sum(1 for s in sentences if len(s) >= 6 and REQUEST.search(s))


def due(session_id: str, minutes: int) -> bool:
    """このセッションで、前に出してから minutes 分たっていれば True にして、今の時刻を覚える。"""
    root = Path(os.environ.get("FANOUT_STATE_DIR") or Path.home() / ".claude" / "state" / "fanout")
    f = root / "nudge.json"
    key = re.sub(r"[^A-Za-z0-9_-]", "", session_id or "")[:60] or "none"
    try:
        seen = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        seen = {}
    now = time.time()
    if now - float(seen.get(key, 0)) < minutes * 60:
        return False
    seen = {k: v for k, v in seen.items() if now - float(v) < 86400}  # 古いセッションの行を残さない
    seen[key] = now
    try:
        root.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(seen), encoding="utf-8")
    except OSError:
        pass
    return True


def main() -> int:
    if os.environ.get("FANOUT_OFF") == "1":
        return 0
    try:
        d = json.load(sys.stdin)
    except ValueError:
        return 0
    prompt = str(d.get("prompt") or "")
    if not prompt.strip() or SYSTEMISH.search(prompt) or CHILD.search(prompt):
        return 0
    n = count_instructions(prompt)
    word = WORDS.search(prompt)
    if n < 2 and not word:
        return 0
    try:
        minutes = max(0, int(os.environ.get("FANOUT_NUDGE_MIN", "15")))
    except ValueError:
        minutes = 15
    if not due(str(d.get("session_id") or ""), minutes):
        return 0
    why = f"独立した指示が {n} 個ある" if n >= 2 else f"「{word.group(0)}」とある"
    print(f"{why}。10 手以上の作業が 2 つ以上なら、子のセッションに分けて並列で進める（fanout.py plan で束・難易度に合うモデル・プロンプトを出す。feedback-session）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
