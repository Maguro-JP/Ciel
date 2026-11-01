#!/usr/bin/env python3
"""judge.py を、作った一覧と一時的なリポジトリで確かめる。"""

import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from judge import judge, load, repo_of  # noqa: E402

NOW = dt.datetime(2026, 11, 1, 0, 0, tzinfo=dt.timezone.utc)


def sess(id, title, status="SESSION_STATUS_IDLE", bucket="SESSION_STATUS_BUCKET_COMPLETED", days=0, **kw):
    return {"id": id, "title": title, "session_status": status, "status_bucket": bucket,
            "updated_at": (NOW - dt.timedelta(days=days)).isoformat().replace("+00:00", "Z"), **kw}


def trig(id, sid, prompt, enabled=True, last="ROUTINE_RUN_STATUS_SUCCEEDED"):
    return {"id": id, "name": prompt, "persistent_session_id": sid, "enabled": enabled, "derived_state": {"prompt": prompt}, "last_run": {"status": last}}


def make_clone(root: Path, name: str, days_ago: int):
    repo = root / name
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    date = (NOW - dt.timedelta(days=days_ago)).isoformat()
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "a"],
                   check=True, env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date, "PATH": "/usr/bin:/bin"})
    subprocess.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", "main"], check=True)
    subprocess.run(["git", "-C", str(repo), "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main"], check=True)
    return repo


class Judge(unittest.TestCase):
    def test_classes_and_actions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_clone(root, "Lazy", days_ago=10)
            make_clone(root, "Busy", days_ago=1)
            sessions = [
                sess("s_lazy", "Lazy 長期開発", days=1),
                sess("s_busy", "Busy 長期開発", days=1),
                sess("s_limit", "Limit", bucket="SESSION_STATUS_BUCKET_FAILED", days=1, post_turn_summary={"status_detail": "You've hit your weekly limit"}),
                sess("s_fail", "Fail", bucket="SESSION_STATUS_BUCKET_FAILED", days=1, post_turn_summary={"status_detail": "error"}),
                sess("s_oldfail", "Old fail", bucket="SESSION_STATUS_BUCKET_FAILED", days=90, origin="ios"),
                sess("s_block", "Block", bucket="SESSION_STATUS_BUCKET_BLOCKED", days=2, post_turn_summary={"needs_action": "答えて"}),
                sess("s_ai", "AI 子", days=5, parent_session_id="s_parent"),
                sess("s_keep", "AI 残す", days=5, parent_session_id="s_parent", tags=["feedback-session:keep"]),
                sess("s_old", "人の古い", days=40, origin="ios"),
                sess("s_new", "人の新しい", days=2, origin="ios"),
                sess("s_arch", "済み", status="SESSION_STATUS_ARCHIVED", days=50),
            ]
            triggers = [trig("t1", "s_lazy", "Maguro-JP/Lazy の long-dev"), trig("t2", "s_busy", "Maguro-JP/Busy の long-dev"),
                        trig("t3", "s_fail", "Maguro-JP/Fail の long-dev"), trig("t4", "s_limit", "Maguro-JP/Limit"),
                        trig("t5", "s_arch", "Maguro-JP/Gone の週 1 回"), trig("t6", "s_gone", "Maguro-JP/Gone2", enabled=False)]
            rows, actions = judge(sessions, triggers, NOW, clones=root, days=3, stale=30, fetch=False)
            v = {r[0]: r[2] for r in rows}
            self.assertEqual(v["Lazy 長期開発"], "サボり")
            self.assertEqual(v["Busy 長期開発"], "回っている")
            self.assertEqual(v["Limit"], "上限で止まった")
            self.assertEqual(v["Fail"], "落ちた")
            self.assertEqual(v["Old fail"], "無駄の候補")
            self.assertEqual(v["Block"], "答え待ち")
            self.assertEqual(v["AI 子"], "無駄")
            self.assertEqual(v["AI 残す"], "待機")
            self.assertEqual(v["人の古い"], "無駄の候補")
            self.assertEqual(v["人の新しい"], "待機")
            self.assertNotIn("済み", v)
            self.assertEqual([a["id"] for a in actions["archive"]], ["s_ai"])
            self.assertEqual(sorted(a["id"] for a in actions["fire"]), ["s_fail", "s_lazy"])
            self.assertEqual(sorted(a["id"] for a in actions["ask"]), ["s_old", "s_oldfail"])
            self.assertIn("s_block", [a["id"] for a in actions["notify"]])
            self.assertIn("t5", [a["id"] for a in actions["notify"]])  # 紐づけ先がアーカイブ済み
            self.assertNotIn("t6", [a["id"] for a in actions["notify"]])  # 無効なものは見ない
            self.assertEqual(v["Maguro-JP/Gone の週 1 回"], "宙に浮いたルーティン")

    def test_load_and_repo_of(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            p.write_text(json.dumps({"ccr": {"data": [{"id": "x"}]}}), encoding="utf-8")
            self.assertEqual(load(str(p)), [{"id": "x"}])
            p.write_text(json.dumps([{"id": "y"}]), encoding="utf-8")
            self.assertEqual(load(str(p)), [{"id": "y"}])
        self.assertEqual(repo_of("Maguro-JP/DigiMon の long-dev。docs/ROADMAP.md を読む"), "DigiMon")
        self.assertIsNone(repo_of("docs/ROADMAP.md だけ"))


if __name__ == "__main__":
    unittest.main()
