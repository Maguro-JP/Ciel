# 魅せる README の節の順と、根拠の決まり

- 日付: 2026-11-07
- 語: README, readme, バッジ, badge, クイックスタート, quick start, standard-readme

## 情報
- standard-readme の仕様は、タイトル、120 文字以内の 1 文、改行で区切ったバッジ、100 行を超えたら目次、code block つきのインストールと使い方、最後にライセンス、を求めている（https://github.com/RichardLitt/standard-readme/blob/main/spec.md 、2026-11-07）
- readme-generator-skill は、リポジトリから読み取れる事実だけを書き、出所の無いバッジや install コマンドを作らず、迷ったら省く決まりを置いている（https://github.com/Moosphan/readme-generator-skill 、2026-11-07）
- Best-README-Template は、バッジを上、ロゴとタイトルを中央、スクリーンショットを説明の直後、はじめ方を前提とインストールに分ける並びにしている（https://github.com/othneildrew/Best-README-Template 、2026-11-07）
- 3 つを読み比べただけで、どの並びが読まれやすいかを数字で確かめてはいない

## 知識
README は入口で、初めて開いた人が 10 秒で「何をする物か、自分に要るか、どう動かすか」を掴めるかで決まる。
だから上から、タイトル、1 文、根拠のあるバッジ、スクリーンショット、特長、5 手以内のクイックスタートの順に置き、ライセンスを最後に置く。
書く中身はリポジトリから読み取れる事実だけにする。無い物を書くと、1 つ嘘が見つかった時点で全部が信用されなくなる。
使えない場合: 文書だけのリポジトリ（インストールと使い方が無い）と、社内だけで使う物（バッジとスクリーンショットが要らない）。

## アルゴリズム
入力は README の本文とリポジトリの根。出力は 10 項目それぞれの OK・NG・注意と、OK の数（点数）。
1. H1 があるか（タイトル）
2. タイトルのあと 5 行以内に、120 文字以内の 1 行があるか（1 文）
3. バッジの画像があり、手元のファイルを指す物は実在するか（バッジ）
4. バッジ以外の画像があり、手元のファイルは実在するか（スクリーンショット）
5. クイックスタートに当たる見出しがあり、code block があり、番号つきの手順が 5 以内か
6. インストールの見出しと code block があるか
7. 使い方の見出しと code block があるか
8. ライセンスの見出しが最後の H2 で、LICENSE のファイルがあるか
9. 相対リンクの先が全部あるか
10. 空の節、置き換え忘れ、100 行を超えて目次が無い、が無いか（仕上げ）
端の場合: README が無ければ全部 NG。見出しは日本語と英語の両方の呼び方を受ける。費用はファイル 1 本の読みだけ。

## 技術
- 場所: `.claude/skills/readme-showcase/scripts/readme_check.py`（10 項目の検査と点数）
- 場所: `.claude/skills/readme-showcase/assets/README.template.md`（節の順の雛形）
- テスト: `.claude/skills/readme-showcase/scripts/test_readme_check.py`

## 実装
- precheck の readme の段に入れ、README が差分にあるときに点数を注意で出す
- Ciel 自身の README に当てた出力: `README 注意: 点数 5/10（NG 4、注意 1）。直す目安: バッジ、スクリーンショット、クイックスタート、インストール、仕上げ`
- repo-management の段 3 が同じ検査を呼ぶ
