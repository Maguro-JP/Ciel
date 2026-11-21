#!/usr/bin/env python3
"""measure_hooks.py を、このリポジトリの settings.json と、作った settings.json で確かめる。"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MEASURE = HERE / "measure_hooks.py"
SETTINGS = ROOT / ".claude" / "settings.json"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.homedir = self.dir / "home"
        (self.homedir / ".claude" / "state").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def measure(self, *args, **env):
        e = dict(os.environ, HOME=str(self.homedir), CLAUDE_PROJECT_DIR=str(ROOT), **env)
        return subprocess.run([sys.executable, "-I", str(MEASURE), *args], cwd=str(ROOT), capture_output=True, text=True, timeout=600, env=e)

    def snapshot(self, top: Path) -> dict:
        return {str(p.relative_to(top)): p.read_bytes() for p in sorted(top.rglob("*")) if p.is_file()}


class Isolation(Base):
    def test_measuring_does_not_write_to_the_real_state(self):
        # 測定の実行が本物の metrics.jsonl に行を足すと、週 1 回の数（短い一言、同じ指示の 2 回目）が測定の行で埋まる
        state = self.homedir / ".claude" / "state"
        for name in ("user-emotion", "prompt-from-context", "verify-before-done", "token-efficiency", "no-fake", "common-sense"):
            (state / name).mkdir()
            (state / name / "metrics.jsonl").write_text(json.dumps({"session": "real", "n": 1}) + "\n", encoding="utf-8")
        named = self.dir / "named"  # 呼んだ側が置き場を環境変数で決めている場合。そこにも書かない
        named.mkdir()
        (named / "metrics.jsonl").write_text(json.dumps({"session": "real"}) + "\n", encoding="utf-8")
        before = self.snapshot(state), self.snapshot(named)
        r = self.measure(str(SETTINGS), USER_EMOTION_STATE=str(named), PROMPT_FROM_CONTEXT_STATE=str(named), TOKEN_EFFICIENCY_STATE=str(named))
        self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)  # 1 は目安の超過。測れてはいる
        self.assertIn("UserPromptSubmit 合計", r.stdout)
        after = self.snapshot(state), self.snapshot(named)
        self.assertEqual(sorted(before[0]), sorted(after[0]), "本物の置き場にファイルが増えた")
        for k in before[0]:
            self.assertEqual(before[0][k], after[0][k], f"本物の {k} に書いた")
        self.assertEqual(before[1], after[1], "環境変数で決めた置き場に書いた")
        self.assertEqual(sorted(p.name for p in (self.homedir / ".claude").iterdir()), ["state"])  # 本物の ~/.claude に、ほかの物も作らない


if __name__ == "__main__":
    unittest.main()
