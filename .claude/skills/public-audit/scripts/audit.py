#!/usr/bin/env python3
"""公開リポジトリに出してよいものか調べる。鍵ではなく「名前・連絡先・ID・費用・内部の場所」を見る。

  audit.py --tree                    作業ツリー
  audit.py --diff [<base>..<head>]   差分（省略時は未コミットの変更）
  audit.py --history                 全コミット（追加行、コミットメッセージ、著者、消したファイル）
  audit.py --github <owner/repo>     GitHub 側（説明・Issue と PR の本文とコメント・リリース・設定）
  audit.py --all <owner/repo>        上の全部

  --names <file>   非公開の名前の一覧（1行1つ。owner/repo か名前だけ）。リポジトリの外に置く。
                   省略時は $PUBLIC_AUDIT_NAMES、無ければ ~/.config/public-audit/names.txt
  --show           値を伏せずに出す（手元の端末で自分だけが見るとき）

検出（重大・注意）があれば終了コード 1。情報だけなら 0。
誤検知は行末に `public-audit: ignore`、または .publicallow に1行ずつ
（正規表現は値に対して、`path:<glob>` はファイルに対して）。
鍵やトークンは secret-leak-check の scan.py が見る。ここでは重ねて見ない。
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

IGNORE_MARK = "public-audit: ignore"

# ---- 行のルール ------------------------------------------------------------
# (名前, 正規表現, 深刻度)。深刻度: high=公開リポジトリに置かない / medium=人が見て決める
# セッション URL を ID より先に置く。1つの箇所を2件に数えないため（重なりは先勝ち）。
RULES = [
    ("セッションの URL",       r"claude\.ai/code/session_[A-Za-z0-9]+", "high"),
    ("セッション・Routine の ID", r"\b(?:session|cse|trig|env|ccpool)_01[A-Za-z0-9]{20,}\b", "high"),
    # 直前が : や / なら URL の認証情報（secret-leak-check の領分）なので拾わない
    ("メールアドレス",         r"(?<![\w.:/+%-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}", "high"),
    ("利用者名入りのパス",     r"(?:/Users/|/home/)(?!(?:user|users|runner|ubuntu|root|node|app|git|work|ec2-user|<)[/\b])[A-Za-z0-9._-]+/", "high"),
    ("利用者名入りのパス",     r"[A-Za-z]:[\\/]Users[\\/](?!(?:Public|Default|<)\b)[^\\/\s\"'<>|]+[\\/]", "high"),
    ("郵便番号・住所",         r"〒\s?\d{3}-?\d{4}", "high"),
    ("電話番号",               r"(?<![\d-])(?:\+81[- ]?\d{1,4}|0\d{1,4})-\d{1,4}-\d{3,4}(?![\d-])", "medium"),
    ("私有アドレス",           r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b(?![.\d])", "medium"),
    ("グローバルアドレス",     r"(?<![\d.])(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-5])(?:\.(?:\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])){3}(?![\d.])", "medium"),
    ("内部ホスト名",           r"(?<![\w.@/-])[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:local|lan|internal|intra|corp|home|private)(?![\w.-])", "medium"),
    ("非公開サービスへのリンク", r"https?://(?:(?:docs|drive|sheets|sites)\.google\.com|(?:www\.)?notion\.so|[a-z0-9-]+\.slack\.com/archives|(?:www\.)?figma\.com/(?:file|design|board)|[a-z0-9-]+\.atlassian\.net|[a-z0-9-]+\.sharepoint\.com)/\S+", "medium"),
    ("費用の数字",             r"(?<![\w$\"'`{(])[$¥€£]\s?(?:\d{1,3}(?:,\d{3})+|\d+\.\d{1,2}|\d{2,})(?![\w}])", "medium"),
    ("費用の数字",             r"(?<![\w.])\d[\d,]*(?:\.\d+)?\s?(?:円|ドル|USD|JPY|EUR)(?![\w])", "medium"),
]

# 値がこれなら出さない。公開前提のもの、例示、容器の中の既定の名前
ALLOW_DEFAULT = [
    r"^(?:no-?reply|noreply)[\w.+-]*@",            # 返信不可のアドレスは個人を指さない
    r"@users\.noreply\.github\.com$",
    r"(?:^|[@.])(?:example|test|invalid|localhost)(?:\.[a-z]+)*$",  # 例示用のドメイン（RFC 2606）
]

# 文書の例示に使うアドレス（RFC 5737）、ループバック、リンクローカル、全ゼロ、マルチキャスト
def ip_is_reserved(v: str) -> bool:
    try:
        a, b, *_ = (int(x) for x in v.split("."))
    except ValueError:
        return True
    if a in (0, 127, 255) or a >= 224:
        return True
    if a == 169 and b == 254:
        return True
    if (a, b) == (192, 0) or (a, b) == (198, 51) or (a, b) == (203, 0):
        return True
    return False

# ---- ファイル名のルール ----------------------------------------------------
# (名前, glob の列, 深刻度)。info は「人が中を見る」の一覧に出す
FILE_RULES = [
    ("認証情報のファイル", ["*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "id_rsa*", "id_ed25519*", "id_ecdsa*",
                           ".npmrc", ".netrc", ".pypirc", ".htpasswd", "kubeconfig", "*.kubeconfig",
                           "credentials.json", "service-account*.json", "*.secret", "secrets.*"], "high"),
    (".env の実体",        [".env", ".env.*"], "high"),
    ("データの持ち出し",   ["*.sqlite", "*.sqlite3", "*.db", "*.sql", "*.har", "*.log", "*.csv", "*.xlsx", "*.pcap"], "medium"),
    ("画像・動画・PDF",    ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.mp4", "*.mov", "*.pdf"], "info"),
]
FILE_EXEMPT = (".example", ".sample", ".template", ".dist")

SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "__pycache__",
             ".venv", "venv", ".next", "target", "corpus"}
SKIP_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
              "Cargo.lock", "go.sum", "Gemfile.lock", "composer.lock"}
BINARY_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".woff", ".woff2",
                 ".ttf", ".zip", ".gz", ".tar", ".mp4", ".mov", ".sqlite", ".sqlite3", ".db", ".p12", ".pfx", ".jks"}


def run(cmd, check=False):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip() or f"{cmd[0]} が失敗")
    return r.stdout


def redact(s: str) -> str:
    """値を全部は出さない。報告が新しい漏れの経路になるため。"""
    if "@" in s:
        local, _, dom = s.partition("@")
        return f"{local[:1]}…@{dom[:1]}…{dom[dom.rfind('.'):] if '.' in dom else ''}"
    if len(s) > 10:
        return s[:3] + "…" + s[-2:]
    return s[:2] + "…"


# ---- 許可と名前の一覧 -------------------------------------------------------
class Allow:
    def __init__(self):
        self.values = [re.compile(p) for p in ALLOW_DEFAULT]
        self.paths = []
        p = Path(".publicallow")
        if p.exists():
            for l in p.read_text(errors="replace").splitlines():
                l = l.strip()
                if not l or l.startswith("#"):
                    continue
                if l.startswith("path:"):
                    self.paths.append(l[5:].strip())
                else:
                    try:
                        self.values.append(re.compile(l))
                    except re.error:
                        self.values.append(re.compile(re.escape(l)))

    def value_ok(self, v: str) -> bool:
        return any(r.search(v) for r in self.values)

    def path_skip(self, path: str) -> bool:
        q = Path(path)
        if any(part in SKIP_DIRS for part in q.parts) or q.name in SKIP_NAMES:
            return True
        return any(q.match(g) for g in self.paths)


def load_names(arg, self_repo):
    """非公開の名前の一覧。見つからなければ None（検査しなかった、と報告する）。"""
    cands = [arg, os.environ.get("PUBLIC_AUDIT_NAMES"), str(Path.home() / ".config/public-audit/names.txt")]
    src = next((c for c in cands if c and Path(c).expanduser().exists()), None)
    if not src:
        return None, None
    pats = []
    for l in Path(src).expanduser().read_text(errors="replace").splitlines():
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        if self_repo and l.lower() in (self_repo.lower(), self_repo.split("/")[-1].lower()):
            continue  # 調べているリポジトリ自身は公開なので除く
        full = re.escape(l)
        pats.append(re.compile(rf"(?<![\w-]){full}(?![\w-])", re.I))
        if "/" in l:
            name = l.split("/")[-1]
            if len(name) >= 4:  # 短い名前は普通の語とぶつかる
                pats.append(re.compile(rf"(?<![\w/-]){re.escape(name)}(?![\w-])", re.I))
    return pats, src


def self_repo_name():
    url = run(["git", "remote", "get-url", "origin"]).strip()
    m = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?$", url)
    return m.group(1) if m else None


# ---- 走査 -------------------------------------------------------------------
class Audit:
    def __init__(self, allow, names, show):
        self.allow, self.names, self.show = allow, names, show
        self.findings = []   # (sev, where, locs, name, value, state)。同じ値は1件にまとめ、場所を並べる
        self.infos = []      # (where, text)
        self.seen = {}
        self.unchecked = []  # 確かめていないこと

    def add(self, sev, where, loc, name, value, state):
        k = (where, name, value if sev != "info" else loc)
        if k in self.seen:
            locs = self.seen[k][2]
            if loc not in locs:
                locs.append(loc)
            return
        f = (sev, where, [loc], name, value, state)
        self.seen[k] = f
        self.findings.append(f)

    def scan_line(self, line, where, loc, state):
        if IGNORE_MARK in line:
            return
        taken = []

        def overlaps(a, b):
            return any(not (b <= x or a >= y) for x, y in taken)

        for name, pat, sev in RULES:
            for m in re.finditer(pat, line):
                v = m.group(0)
                if overlaps(*m.span()) or self.allow.value_ok(v):
                    continue
                if name == "グローバルアドレス" and ip_is_reserved(v):
                    continue
                taken.append(m.span())
                self.add(sev, where, loc, name, v, state)
        if self.names:
            for pat in self.names:
                for m in pat.finditer(line):
                    if overlaps(*m.span()):
                        continue
                    taken.append(m.span())
                    self.add("high", where, loc, "非公開リポジトリの名前", m.group(0), state)

    def scan_filename(self, path, where, state, exists=True):
        q = Path(path)
        if any(q.name.endswith(x) or x in q.name for x in FILE_EXEMPT):
            return
        for name, globs, sev in FILE_RULES:
            if any(q.match(g) for g in globs):
                note = "" if exists else "（消したが履歴に残る）"
                self.add(sev, where, path + note, name, q.name, state)
                return

    # 作業ツリー
    def tree(self):
        # 追跡していないファイルも見る。次の git add で入るものは「これから出すもの」
        files = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"]).splitlines() \
            or [str(p) for p in Path(".").rglob("*") if p.is_file()]
        for f in files:
            if self.allow.path_skip(f):
                continue
            self.scan_filename(f, "作業ツリー", "まだ止められる")
            if Path(f).suffix.lower() in BINARY_SUFFIX:
                continue
            try:
                text = Path(f).read_text(errors="replace")
            except (OSError, IsADirectoryError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                self.scan_line(line, "作業ツリー", f"{f}:{i}", "まだ止められる")

    # 差分
    def diff(self, rng):
        cmd = ["git", "diff", "--unified=0"] + ([rng] if rng else ["HEAD"])
        path, ln = "?", 0
        for line in run(cmd).splitlines():
            if line.startswith("+++ b/"):
                path = line[6:]
                if not self.allow.path_skip(path):
                    self.scan_filename(path, "差分", "まだ止められる")
            elif line.startswith("@@"):
                m = re.search(r"\+(\d+)", line)
                ln = int(m.group(1)) if m else 0
            elif line.startswith("+") and not line.startswith("+++"):
                if not self.allow.path_skip(path):
                    self.scan_line(line[1:], "差分", f"{path}:{ln}", "まだ止められる")
                ln += 1

    # 履歴
    def history(self):
        state = "すでに公開（push 済みなら）"
        # 追加行
        for sha in run(["git", "rev-list", "--all"]).split():
            path = "?"
            for line in run(["git", "show", "--unified=0", "--format=", sha]).splitlines():
                if line.startswith("+++ b/"):
                    path = line[6:]
                elif line.startswith("+") and not line.startswith("+++"):
                    if not self.allow.path_skip(path) and Path(path).suffix.lower() not in BINARY_SUFFIX:
                        self.scan_line(line[1:], "履歴", f"{sha[:8]}:{path}", state)
        # コミットメッセージと著者
        authors = {}
        raw = run(["git", "log", "--all", "--date=iso-strict", "--format=%H%x1f%an%x1f%ae%x1f%ad%x1f%B%x1e"])
        for rec in raw.split("\x1e"):
            if not rec.strip():
                continue
            sha, an, ae, ad, body = (rec.lstrip("\n").split("\x1f", 4) + [""] * 5)[:5]
            tz = ad[-6:] if len(ad) >= 6 else "?"
            a = authors.setdefault((an, ae), {"n": 0, "tz": set()})
            a["n"] += 1
            a["tz"].add(tz)
            for i, line in enumerate(body.splitlines(), 1):
                self.scan_line(line, "履歴", f"{sha[:8]}:コミットメッセージ", state)
        for (an, ae), a in sorted(authors.items(), key=lambda x: -x[1]["n"]):
            shown = ae if self.show or self.allow.value_ok(ae) else redact(ae)
            self.infos.append(("履歴", f"著者 {an} <{shown}> {a['n']} コミット、時差 {' '.join(sorted(a['tz']))}"))
            if not self.allow.value_ok(ae) and "@" in ae:
                self.add("high", "履歴", "著者のメールアドレス", "メールアドレス", ae, state)
        # 一度でも追加されたファイル名
        present = set(run(["git", "ls-files"]).splitlines())
        ever = set(run(["git", "log", "--all", "--diff-filter=A", "--name-only", "--format="]).split("\n"))
        for f in sorted(x for x in ever if x):
            if not self.allow.path_skip(f):
                self.scan_filename(f, "履歴", state, exists=f in present)

    # GitHub 側
    def github(self, repo):
        where = "GitHub"
        try:
            meta = json.loads(run(["gh", "api", f"repos/{repo}"], check=True))
        except Exception as e:  # noqa: BLE001
            self.unchecked.append(f"GitHub 側（{repo}）: gh api が使えなかった。{str(e)[:120]}")
            return None
        public = not meta.get("private", True)
        state = "すでに公開" if public else "まだ非公開（公開すると見える）"
        for k in ("description", "homepage"):
            if meta.get(k):
                self.scan_line(str(meta[k]), where, f"リポジトリの {k}", state)
        for t in meta.get("topics") or []:
            self.scan_line(t, where, "リポジトリの topic", state)
        for flag, text in (("has_wiki", "Wiki が有効。中身は API で読めないので人が見る"),
                           ("has_pages", "Pages が有効。公開サイトの中身を人が見る"),
                           ("has_discussions", "Discussions が有効。投稿を人が見る"),
                           ("fork", "fork。上流にも同じ履歴がある")):
            if meta.get(flag):
                self.infos.append((where, text))

        def pages(path, cap=10):
            for page in range(1, cap + 1):
                sep = "&" if "?" in path else "?"
                try:
                    out = run(["gh", "api", f"{path}{sep}per_page=100&page={page}"], check=True)
                except Exception as e:  # noqa: BLE001
                    self.unchecked.append(f"GitHub 側 {path}: {str(e)[:120]}")
                    return
                items = json.loads(out or "[]")
                if not isinstance(items, list) or not items:
                    return
                yield from items
                if len(items) < 100:
                    return
            self.unchecked.append(f"GitHub 側 {path}: {cap * 100} 件で打ち切った")

        for it in pages(f"repos/{repo}/issues?state=all"):
            kind = "PR" if it.get("pull_request") else "Issue"
            loc = f"{kind} #{it['number']}"
            self.scan_line(it.get("title") or "", where, f"{loc} 題", state)
            for line in (it.get("body") or "").splitlines():
                self.scan_line(line, where, f"{loc} 本文", state)
        for path, label in ((f"repos/{repo}/issues/comments", "コメント"),
                            (f"repos/{repo}/pulls/comments", "レビューコメント")):
            for c in pages(path):
                num = (c.get("issue_url") or c.get("pull_request_url") or "").rsplit("/", 1)[-1]
                for line in (c.get("body") or "").splitlines():
                    self.scan_line(line, where, f"#{num} {label}", state)
        for r in pages(f"repos/{repo}/releases"):
            for line in ((r.get("name") or "") + "\n" + (r.get("body") or "")).splitlines():
                self.scan_line(line, where, f"リリース {r.get('tag_name', '')}", state)
        try:
            wf = json.loads(run(["gh", "api", f"repos/{repo}/actions/workflows"], check=True))
            names = [w.get("path", "") for w in wf.get("workflows", [])]
            if names:
                self.infos.append((where, f"Actions のログは公開リポジトリでは誰でも読める。workflow {len(names)} 本: {', '.join(names)}。env や設定を echo していないか人が見る"))
        except Exception:  # noqa: BLE001
            self.unchecked.append("GitHub 側 actions/workflows: 読めなかった")
        return public

    # 報告
    def report(self, labels):
        print(f"== public-audit: {' / '.join(labels)} ==")
        order = {"high": 0, "medium": 1, "info": 2}
        mark = {"high": "!!", "medium": " ?", "info": "--"}
        jp = {"high": "重大", "medium": "注意", "info": "情報"}
        fs = sorted(self.findings, key=lambda f: (order[f[0]], f[1], f[2][0]))
        images = [f for f in fs if f[0] == "info"]
        for sev, where, locs, name, value, state in fs:
            if sev == "info":
                continue
            shown = value if self.show else redact(value)
            loc = "; ".join(locs[:3]) + (f" 他 {len(locs) - 3} 箇所" if len(locs) > 3 else "")
            print(f"  {mark[sev]} [{jp[sev]}] {name}\n       {loc}（{where}、{state}）\n       {shown}")
        if images:
            by_where = {}
            for f in images:
                by_where.setdefault(f[1], []).append(f[2][0])
            for where, locs in by_where.items():
                head = ", ".join(locs[:8]) + ("…" if len(locs) > 8 else "")
                print(f"  -- [情報] 画像・動画・PDF {len(locs)} 件（{where}）。名前や画面の URL が写っていないか人が見る: {head}")
        for where, text in self.infos:
            print(f"  -- [情報] {text}（{where}）")
        for u in self.unchecked:
            print(f"  ?? [確かめていない] {u}")
        high = sum(1 for f in fs if f[0] == "high")
        med = sum(1 for f in fs if f[0] == "medium")
        stop = sum(1 for f in fs if f[0] != "info" and f[5].startswith("まだ"))
        gone = sum(1 for f in fs if f[0] != "info" and f[5].startswith("すでに"))
        print(f"\n  重大 {high} / 注意 {med} / 情報 {len(images) + len(self.infos)}")
        print(f"  まだ止められる {stop} / すでに公開 {gone}（履歴と GitHub 側のもの。消しても fork やキャッシュに残る）")
        if not self.names:
            print("  非公開の名前は検査していない（--names か ~/.config/public-audit/names.txt が無い）")
        if high + med == 0:
            print("  このルールでは検出されなかった。人にしか分からないもの（人名、内部の決定、未公開の計画）は references/checklist.md で見る")
        return 1 if high + med else 0


def main():
    ap = argparse.ArgumentParser(add_help=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--tree", action="store_true")
    g.add_argument("--diff", nargs="?", const="", metavar="RANGE")
    g.add_argument("--history", action="store_true")
    g.add_argument("--github", metavar="OWNER/REPO")
    g.add_argument("--all", metavar="OWNER/REPO")
    ap.add_argument("--names", metavar="FILE")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    allow = Allow()
    self_repo = a.github or a.all or self_repo_name()
    names, src = load_names(a.names, self_repo)
    au = Audit(allow, names, a.show)
    labels = []
    if a.all:
        au.tree(); labels.append("作業ツリー")
        au.history(); labels.append("履歴")
        au.github(a.all); labels.append(f"GitHub {a.all}")
    elif a.history:
        au.history(); labels.append("履歴（全コミット）")
    elif a.github:
        au.github(a.github); labels.append(f"GitHub {a.github}")
    elif a.diff is not None:
        au.diff(a.diff or None); labels.append(f"差分 {a.diff or 'HEAD'}")
    else:
        au.tree(); labels.append("作業ツリー")
    if src:
        au.infos.append(("名前", f"非公開の名前の一覧: {src}（{len(names)} 件の形）"))
    return au.report(labels)


if __name__ == "__main__":
    sys.exit(main())
