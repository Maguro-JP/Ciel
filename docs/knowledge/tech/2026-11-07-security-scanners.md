# 検査は実績のあるツールを先に使い、同じ行の検出を 1 つに畳む

- 日付: 2026-11-07
- 語: bandit, ruff, semgrep, shellcheck, detect-secrets, gitleaks, 脆弱性, 検査, 重さ

## 情報
- Bandit は検出を B 番号で持つ（B105 直書きのパスワード、B301 pickle、B501 証明書の検証を切る、B506 yaml.load、B602 shell=True）（https://github.com/PyCQA/bandit 、2026-11-07）
- ruff の S の規則は flake8-bandit の移植で、`ruff check --select S --output-format json` で同じ型を出せる（https://github.com/astral-sh/ruff 、2026-11-07）
- 動かして確かめた: pip の --user で ruff、bandit、semgrep、shellcheck-py、detect-secrets、pip-audit が入り、proxy 越しに semgrep の registry（p/security-audit）と gitleaks の Releases も取れた
- 動かして確かめた: 同じ 1 行（shell=True）を bandit、ruff、semgrep がそれぞれ別の番号で出し、3 件に数えられた
- 動かして確かめた: detect-secrets のエントロピーだけの検出は、要約の digest やコミットの SHA にも鳴った

## 知識
自前の正規表現は、知られた穴の型の一部しか見ない。実績のあるツールは型が多く、偽の検出の扱いも練られているので、先に入れて使う。
ただし複数のツールを重ねると同じ行が何度も数えられ、数が現実より大きく見える。場所（ファイルと行）で 1 つに畳み、重い方の重さを残す。
ツールごとに重さの言葉が違う（HIGH、ERROR、error）ので、自分の 3 段（重大・注意・情報）に写す表を 1 か所に置く。
使えない場合: ツールを入れられない環境（外に出られない、pip が無い）。そのときだけ正規表現で補い、何で見て何が無かったかを出力の先頭に出す。
エントロピーだけの検出は鍵と決めつけず、注意に落とす。

## アルゴリズム
入力はリポジトリの根と対象のファイルの列。出力は検出の列（重さ、ファイル、行、番号、何、直し方）と、使ったツール・無いツールの 1 行。
1. ツールの有無を調べる（PATH と ~/.local/bin）
2. 言語ごとに、あるツールを全部動かす（Python は bandit と ruff、Python と JS は semgrep）
3. ツールの出力のパスを根からの相対にそろえる（./x、絶対、相対が混ざる）
4. 重さを写す（bandit の HIGH と MEDIUM、semgrep の ERROR は重大。LOW と WARNING は注意）
5. 抑止の印（行末の code-check: ignore）のある行を外す
6. ツールが 1 つも見ていない言語だけ、正規表現を動かす
7. 同じファイルの同じ行の検出を 1 つに畳み、他の番号を「＋番号」で足し、重い方の重さにする
端の場合: ツールの出力が JSON として読めなければその回を飛ばす。registry が取れなければ同梱の規則で動かす。テストのファイルは型の検査をしない。

## 技術
- 場所: `.claude/skills/code-check/scripts/tools.py`（ツールの一覧、有無、導入）
- 場所: `.claude/skills/code-check/scripts/vuln_scan.py` の `scan`（ツールを先に、無い言語だけ正規表現）
- 場所: `.claude/skills/code-check/scripts/common.py` の `dedupe` と `relpath`（畳み込みとパスのそろえ）
- テスト: `.claude/skills/code-check/scripts/test_vuln_scan.py`

## 実装
- precheck の crash・vuln・info の段と、repo-management の段 10〜12 に入れた
- Ciel 自身に当てた出力: `コードの確認: 重大 0 / 注意 78 / 情報 2`
- 畳み込みのテストの出力: 3 つのツールと正規表現が同じ行を出しても `bad.py:2` は 1 行
