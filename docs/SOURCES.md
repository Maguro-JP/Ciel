# 取り込んだ公開スキルと道具

作る前に、公開されているスキルを探す。使えるものは取り込み、Ciel の決まりに合わせて改善し、ここに出典を書く。
取り込んだファイルには先頭に出典とライセンスを書く。要点だけを写した資料も、出典を節の冒頭に書く。

| 元 | ライセンス | 取り込み先 | 取り込んだもの | Ciel で変えたこと |
|---|---|---|---|---|
| [tomkd555/prose-lint](https://github.com/tomkd555/prose-lint) | MIT, Copyright (c) 2026 tomkd555 | `ja-proofread` | textlint の層の組み方と設定（`assets/textlint/.textlintrc.json`）、公用文のかな辞書 `prh/koyobun-kana.yml`、副詞の辞書 `dict/fukushi.yml`、翻訳調のマーカー 13 種（`references/translationese.md`） | 数字と助数詞の空白、スラッシュ、記録の行末は見ない。1文の長さは 100 文字。英語用の vale は取り込まない |
| [lostandfound/textlint-rule-ja-hiragana-fukushi](https://github.com/lostandfound/textlint-rule-ja-hiragana-fukushi) | MIT, Copyright (c) Hiroshi Takase | `ja-proofread/assets/textlint/dict/fukushi.yml` | 副詞の辞書（prose-lint 経由。公用文で漢字のままの5語を除いたもの） | 無し |
| [kojikojikojikoji/natural-japanese-writing](https://github.com/kojikojikojikoji/natural-japanese-writing) | MIT, Copyright (c) 2025 Siqi Chen | `ja-proofread/scripts/ai_habits.py` | `scripts/check.py` をそのまま同梱。6 層の点検の要点を `references/translationese.md` に | proofread.py から文書ごとに呼び、★ の数と目印を1行で出す |
| [coji/natural-japanese](https://github.com/coji/natural-japanese) | MIT, Copyright (c) 2026 coji | `ja-proofread/references/translationese.md` | 「元にない内容を足さない」規則、中身の見えない言い回しの 7 型と直し方、打ち消しの 3 種類、演出語の削り方 | 要点だけ。`lint.py`（sudachipy）は取り込まず、プラグインとして入れれば使う |
| [MaryCache/ja-cold-reader](https://github.com/MaryCache/ja-cold-reader) | MIT, Copyright (c) 2026 MaryCache | `ja-proofread/references/cold-reader.md` | 文脈を持たない読み手への指示文と 6 つの型、自己点検の問い | Ciel の手順（Agent ツールで新しい文脈）に合わせた。`restate_check.py` と line-layout は取り込まない |
| [B16B1RD/bb-doc-skills](https://github.com/B16B1RD/bb-doc-skills) | MIT, Copyright (c) 2026 B16B1RD | `ja-proofread/references/rules.md` | PR 本文の 4 つの役割（`tech-write/references/pr.md`） | 要点だけ |
| [wshuyi/skill-publisher-skill](https://github.com/wshuyi/skill-publisher-skill) | MIT, Copyright (c) 2024 wshuyi | `content-audit` | 比べただけ。取り込み無し | `localhost:<port>` の検出は候補に残す |
| [denfry/claude-skills](https://github.com/denfry/claude-skills) `token-efficiency` | MIT, Copyright (c) 2026 denfry | `token-efficiency` | 3層の設計、CORE の決まり、フック3本（`hooks/`）、7つの節の骨組み | 文言を日本語にし、CORE に Ciel の会話の形と MCP の一覧の決まりを足した。`context_budget.py` と `install.py` は取り込まず、settings.json に直接書く |
| [scottspence.com「how to make claude code follow hook instructions」](https://scottspence.com/posts/how-to-make-claude-code-follow-hook-instructions) | 記事（参考のみ） | `follow-instructions` | フックで差し込んだ決まりが長い会話で無視されること、CLAUDE.md に「フックの指示は必ず守る」と書くと戻るという観察 | コードは無し。同じ目的の公開スキルは見つからなかった（2026-10-24） |
| [validkeys/sherpy](https://github.com/validkeys/sherpy) `definition-of-done` | MIT, Copyright (c) 2025 Sherpy Contributors | `finish-first` | 完成条件を「確かめられる文」で書く基準（「login works」ではなく「メールとパスワードでログインできる」）と、出口のチェックリストの形 | milestones.yaml と要件ファイルの仕組みは取り込まず、Markdown の表1枚にした |
| [claudskills.com `definition-of-done`](https://claudskills.com/skills/definition-of-done/) | ライセンス表記なし（参考のみ） | `finish-first` | 「意図・途中・かけた時間・記憶・それらしい答えは完成ではない」の5つの観点 | 文言は取り込まず要点だけ。チェックリストの項目は取り込まない |
| [claudskills.com `intent-executor`](https://claudskills.com/skills/intent-executor/) | ライセンス表記なし（参考のみ） | `prompt-from-context` | 曖昧な一言から意図を推定して動く、という目的。「推定して、確認して、実行する」の3段のうち前後の2段 | 確認で止める段は取り込まない（聞き返さない）。手順の本文は公開ページに無く、読んでいない |
| sync-docs、update-project、docs-workflow、consistency-enforcement（公開スキルの登録サイトの一覧） | ライセンス表記なし（参考のみ） | `docs-upkeep` | 言及先の実在を検査する、README の一覧を正として他の文書と突き合わせる、の 2 つの考え | 手順の文だけで検査のコードは無い。コードは `docs_check.py` に自分で書いた |
| 用語集を保守する公開スキル（公開スキルの登録サイトの一覧。glossary、terminology の名前のもの） | ライセンス表記なし（参考のみ） | `user-terms` | 用語集を 1 か所に置き、書く側がそれを読む、という形だけ | 読ませるだけでは直らなかったので、取り込み無し。ユーザーの発言から語を数え、Stop フックで止める仕組みは自分で書いた（2026-10-26。同じ目的の公開スキルは見つからなかった） |
| [Cornjebus/security-analyzer](https://github.com/Cornjebus/security-analyzer) | MIT | `vuln-watch` | 出どころを重ねる考え（OSV と CISA KEV を合わせ、悪用済みを重さより上に置く）。危険度の式（CVSS・悪用・重要度・露出の重み付け） | コードは読んでいない。式は取り込まず、GitHub の判定か CVSS の基本値と「悪用済み」の 2 軸にした。棚卸しは全リポジトリを 1 回で見る形に自分で書いた |
| dependency-cve-audit、osv-scanner-dependency-vulnerability-detector、weekly-dep-audit（公開スキルの登録サイトの一覧） | ライセンス表記なし（参考のみ） | `vuln-watch` | npm の lock を OSV に当てる、週 1 回で複数のリポジトリを見る、の 2 つの考え | 手順の文だけで取り込み無し。JVN（日本語）と GitHub Actions の浮いたタグの扱いは自分で足した |
| [OSV](https://osv.dev)、[CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)、[JVN](https://jvn.jp) | データの出どころ（API と RSS） | `vuln-watch/scripts/scan.py` | 脆弱性と悪用済みの一覧とニュース | 取ったものは `~/.cache/vuln-watch` に写しを置き、リポジトリには入れない |
| [valorisa/Claude-Skills](https://github.com/valorisa/Claude-Skills) `token-optimization` | MIT, Copyright (c) 2026 valorisa | `token-efficiency` | 消費の4つの出どころ、途中で道具を足さない | 要点だけ |
| [obra/superpowers](https://github.com/obra/superpowers) `subagent-driven-development` | MIT, Copyright (c) 2025 Jesse Vincent | `token-efficiency` | 文脈を渡さないサブエージェントの考え方 | 要点だけ |
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Apache-2.0 | 無し | 参考だけ。出力を電報のように縮める方式は「助詞のある文」の決まりと合わない | 取り込み無し |
| textlint と各規則（npm） | それぞれのライセンス（MIT） | `~/.cache/ciel-textlint` | `scripts/setup-textlint.sh` で npm から入れる。リポジトリには入れない | 無し |

## 探し方

1. WebSearch で「Claude Code skill SKILL.md <題>」「github claude skills <題>」を日本語と英語で検索する
2. `scripts/collect-corpus.sh` の提供元（anthropics/skills、obra/superpowers、google/skills など）と、awesome-claude-skills の一覧を見る
3. 候補を `git clone --depth 1` で読む。SKILL.md、LICENSE、scripts、references
4. ライセンスを確かめる。MIT と Apache-2.0 は著作権表示を残せば取り込める。ライセンスの無いものは取り込まず、参考に留める
5. 取り込んだら、この表と、取り込み先の SKILL.md の「取り込んだ公開スキル」に書く

改善は Ciel の中で行う。元のリポジトリに返すかは、変更が元の利用者にも役立つときにユーザーが決める。
