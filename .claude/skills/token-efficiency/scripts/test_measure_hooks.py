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


class Delivered(unittest.TestCase):
    def test_only_what_reaches_the_context_is_counted(self):
        sys.path.insert(0, str(HERE))
        import measure_hooks as m
        ctx = json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "あいうえお"}})  # 既定は ASCII に逃がすので、標準出力は長い
        self.assertEqual(m.delivered("PostToolUse", 0, ctx, ""), "あいうえお")
        self.assertEqual(m.delivered("UserPromptSubmit", 0, ctx, ""), "あいうえお")
        self.assertEqual(m.delivered("UserPromptSubmit", 0, "決まり: 短く書く\n", ""), "決まり: 短く書く\n")  # 素の標準出力が届くのは、開始と入力のときだけ
        self.assertEqual(m.delivered("SessionStart", 0, "開始の文\n", "警告"), "開始の文\n")
        self.assertEqual(m.delivered("PostToolUse", 0, "素の標準出力は届かない\n", ""), "")
        self.assertEqual(m.delivered("Stop", 0, "素の標準出力は届かない\n", ""), "")
        self.assertEqual(m.delivered("Stop", 2, "", "根拠の無い完了がある。\n"), "根拠の無い完了がある。")  # 止めるフックは、標準エラーが戻る
        self.assertEqual(m.delivered("Stop", 0, json.dumps({"decision": "block", "reason": "足りない 1 行を足す"}), ""), "足りない 1 行を足す")
        self.assertEqual(m.delivered("Stop", 0, json.dumps({"systemMessage": "端末に出るだけの文"}), ""), "")
        self.assertEqual(m.delivered("PostToolUse", 1, "", "Traceback"), "")  # 落ちたフックの文は届かない

    def test_matcher(self):
        sys.path.insert(0, str(HERE))
        import measure_hooks as m
        self.assertTrue(m.matches(None, "Bash"))
        self.assertTrue(m.matches("", "Bash"))
        self.assertTrue(m.matches("*", "Write"))
        self.assertTrue(m.matches("Edit|Write|MultiEdit", "Write"))
        self.assertTrue(m.matches("Bash|mcp__.*", "mcp__github__list_issues"))
        self.assertFalse(m.matches("Edit|Write|MultiEdit", "Bash"))
        self.assertFalse(m.matches("Bash", "BashOutput"))


class Events(Base):
    def settings(self, hooks: dict) -> str:
        p = self.dir / "settings.json"
        p.write_text(json.dumps({"hooks": hooks}, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def hook(self, name: str, body: str) -> str:
        p = self.dir / f"{name}.py"
        p.write_text("import json, sys\nd = json.load(sys.stdin)\n" + body, encoding="utf-8")
        return f"{sys.executable} {p}"

    def test_post_tool_use_and_stop_are_measured_with_samples(self):
        say = "print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': 'あ' * %d}}))\n"
        s = self.settings({
            "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": self.hook("bash100", say % 100)}]},
                            {"matcher": "Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": self.hook("write50", say % 50)},
                                                                         {"type": "command", "command": self.hook("plain", "print('素の標準出力' * 40)\n")}]}],
            "Stop": [{"hooks": [{"type": "command", "command": self.hook("stop80", "print('い' * 80, file=sys.stderr)\nsys.exit(2)\n")},
                                {"type": "command", "command": self.hook("quiet", "sys.exit(0)\n")}]}]})
        r = self.measure(s)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        totals = {ln.split(" 合計 ")[0]: int(ln.split(" 合計 ")[1].split()[0]) for ln in r.stdout.splitlines() if " 合計 " in ln}
        bash = [v for k, v in totals.items() if k.startswith("PostToolUse（Bash")]
        write = [v for k, v in totals.items() if k.startswith("PostToolUse（Write")]
        stop = [v for k, v in totals.items() if k.startswith("Stop（")]
        self.assertTrue(bash and set(bash) == {100}, r.stdout)   # Bash の見本には Bash のフックだけ
        self.assertTrue(write and set(write) == {50}, r.stdout)  # 素の標準出力は数えない
        self.assertTrue(stop and set(stop) == {80}, r.stdout)
        self.assertEqual(totals["SessionStart"], 0)
        self.assertEqual(totals["UserPromptSubmit"], 0)

    def test_over_the_budget_is_reported_and_exits_one(self):
        say = "print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': 'あ' * 100}}))\n"
        s = self.settings({"PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": self.hook("bash100", say)}]}]})
        r = self.measure(s, "--budget", "99")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegex(r.stdout, r"PostToolUse（Bash[^\n]*合計 100 文字（目安 99）: 超過")
        self.assertEqual(self.measure(s, "--budget", "100").returncode, 0)

    def test_the_samples_make_the_real_hooks_speak(self):
        # 見本の入力で、知らせと差し戻しが実際に出ること。出なければ、長さを測ったことにならない
        r = self.measure(str(SETTINGS))
        self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)
        spoke = {}
        for ln in r.stdout.splitlines():
            parts = ln.split()
            if len(parts) >= 3 and parts[0] in ("PostToolUse", "Stop") and parts[1].isdigit():
                name = ln.split(".claude/")[-1]
                spoke[name] = max(spoke.get(name, 0), int(parts[1]))
        for name in ("skills/common-sense/hooks/odd_nudge.py", "skills/bug-first/hooks/crash_nudge.py", "skills/no-fake/hooks/fake_nudge.py",
                     "skills/code-check/hooks/code_nudge.py", "skills/common-sense/hooks/memory_nudge.py", "hooks/pr-nudge.sh",
                     "skills/verify-before-done/hooks/done_check.py", "skills/common-sense/hooks/guess_gate.py", "skills/no-fake/hooks/fake_gate.py"):
            self.assertGreater(spoke.get(name, 0), 0, f"{name} が見本の入力で何も出していない\n{r.stdout}")


if __name__ == "__main__":
    unittest.main()
