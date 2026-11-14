#!/usr/bin/env python3
"""fanout_nudge.py（UserPromptSubmit）と fanout_gate.py（Stop）を、作った入力と transcript で確かめる。"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS))
from fanout_nudge import count_instructions  # noqa: E402

TWO = "1. README を書き直して\n2. フックの判定を直して"
THREE = TWO + "\n3. 一覧を更新して"
CHILD = THREE + "\n# やらないこと\nPR を作らない。セッションやルーティンを作らない・消さない・変えない。"


def run(hook, payload, state, **env):
    e = dict(os.environ, FANOUT_STATE_DIR=state, **env)
    e.pop("FANOUT_OFF", None) if "FANOUT_OFF" not in env else None
    r = subprocess.run([sys.executable, "-I", str(HOOKS / hook)], input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True, env=e)
    return r.returncode, r.stdout, r.stderr


def transcript(path, prompt, calls, tool="Read", text="★ 済み"):
    rows = [{"type": "user", "message": {"content": "前のターン"}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Agent", "input": {}}]}},
            {"type": "user", "message": {"content": prompt}}]
    for i in range(calls):
        rows.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": tool if i == 0 else "Read", "input": {}}]}})
        rows.append({"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}})
    rows.append({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
    Path(path).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return {"session_id": "s", "transcript_path": str(path), "stop_hook_active": False}


class Count(unittest.TestCase):
    def test_count_instructions(self):
        self.assertEqual(count_instructions(TWO), 2)
        self.assertEqual(count_instructions("・README を直す\n・テストを足す\n・配る"), 3)
        self.assertEqual(count_instructions("README を読んで"), 1)
        self.assertEqual(count_instructions("セッションが使われないので改善する。難易度でモデルを切り替える"), 2)
        self.assertEqual(count_instructions("これは何?"), 0)


class Nudge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def nudge(self, prompt, session="s1", **env):
        return run("fanout_nudge.py", {"session_id": session, "prompt": prompt}, self.tmp.name, **env)

    def test_two_instructions_or_a_word(self):
        code, out, _ = self.nudge(TWO)
        self.assertEqual(code, 0)
        self.assertIn("独立した指示が 2 個", out)
        self.assertIn("fanout.py plan", out)
        self.assertLess(len(out), 200)  # 差し込みは 1 行
        self.assertEqual(out.count("\n"), 1)
        self.assertIn("「全部のリポジトリ」", self.nudge("全部のリポジトリに配って", session="s2")[1])
        self.assertIn("「並列」", self.nudge("並列で進めて", session="s3")[1])

    def test_quiet_cases(self):
        self.assertEqual(self.nudge("README を読んで")[1], "")
        self.assertEqual(self.nudge(CHILD)[1], "")  # 子のセッションには出さない
        self.assertEqual(self.nudge("<task-notification>\n1. a して\n2. b して")[1], "")
        self.assertEqual(self.nudge(TWO, FANOUT_OFF="1")[1], "")

    def test_once_per_15_minutes_per_session(self):
        self.assertNotEqual(self.nudge(TWO)[1], "")
        self.assertEqual(self.nudge(TWO)[1], "")  # 同じセッションの 2 回目は黙る
        self.assertNotEqual(self.nudge(TWO, session="other")[1], "")
        self.assertNotEqual(self.nudge(TWO, FANOUT_NUDGE_MIN="0")[1], "")


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name) / "t.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def gate(self, payload, **env):
        return run("fanout_gate.py", payload, self.tmp.name, **env)

    def test_long_turn_with_three_instructions_is_stopped(self):
        code, _, err = self.gate(transcript(self.t, THREE, 41))
        self.assertEqual(code, 2)
        self.assertIn("指示が 3 個", err)
        self.assertIn("❕ 並列: 分けない", err)
        self.assertEqual(err.count("\n"), 1)  # 差し戻しの文は 1 行

    def test_passes(self):
        self.assertEqual(self.gate(transcript(self.t, THREE, 40))[0], 0)  # 40 回ちょうどは通す
        self.assertEqual(self.gate(transcript(self.t, TWO, 60))[0], 0)  # 指示が 2 個
        self.assertEqual(self.gate(transcript(self.t, THREE, 60, tool="Agent"))[0], 0)
        self.assertEqual(self.gate(transcript(self.t, THREE, 60, tool="mcp__claude-code-remote__create_session"))[0], 0)
        self.assertEqual(self.gate(transcript(self.t, THREE, 60, text="★ 済み\n❕ 並列: 分けない（場所が重なる）"))[0], 0)
        self.assertEqual(self.gate(transcript(self.t, CHILD, 60))[0], 0)  # 子のセッションは見ない
        self.assertEqual(self.gate(dict(transcript(self.t, THREE, 60), stop_hook_active=True))[0], 0)
        self.assertEqual(self.gate(transcript(self.t, THREE, 60), FANOUT_OFF="1")[0], 0)
        self.assertEqual(self.gate({"session_id": "s"})[0], 0)

    def test_thresholds_can_be_changed(self):
        self.assertEqual(self.gate(transcript(self.t, TWO, 6), FANOUT_GATE_CALLS="5", FANOUT_GATE_ITEMS="2")[0], 2)

    def test_hook_feedback_is_not_a_new_turn(self):
        payload = transcript(self.t, THREE, 41)
        with open(self.t, "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "message": {"content": "Stop hook feedback: 疑いの行が無い"}}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "❕ 疑い: 無し"}]}}, ensure_ascii=False) + "\n")
        self.assertEqual(self.gate(payload)[0], 2)


if __name__ == "__main__":
    unittest.main()
