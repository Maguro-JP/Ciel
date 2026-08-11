# スキル設計ガイドライン

## 1. description がすべて

スキルは `description` を見て発動するかどうかが決まります。本文がどれだけ良くても、
description が曖昧なら永遠に呼ばれません。

**悪い例**
```yaml
description: PDFを扱うのに便利なスキル
```

**良い例**
```yaml
description: PDFの読み取り・結合・分割・フォーム入力を行うとき。ユーザーが .pdf ファイル名に
  言及したり、PDFの生成を求めたときに使う。画像やWord文書には使わない。
```

書くべきもの：
- 発動する**具体的な状況**とキーワード
- 発動**しない**ケース（誤爆を防ぐ）

## 2. 本文は短く保つ

SKILL.md は発動するたびに読み込まれます。長いほど毎回コストがかかる。

- 中核の手順だけを SKILL.md に
- 詳細な仕様・APIリファレンス・長い例は `references/*.md` に逃がし、
  「必要になったら references/foo.md を読む」と本文から指示する
- 決まりきった処理はドキュメントで説明せず `scripts/` の実行可能ファイルにする

目安：SKILL.md 本文は 500 行以内、できれば 200 行以内。

## 3. ディレクトリ構成

```
skills/<skill-name>/
├── SKILL.md          必須
├── references/       必要に応じて読む長い資料
├── scripts/          実行するスクリプト
└── assets/           テンプレート・画像など
```

## 4. 命名

- ディレクトリ名 = `name` フィールド
- 小文字・数字・ハイフンのみ（`skill-audit`, `pdf-form-filler`）
- 動詞ベースだと発動しやすい（`review-x` `generate-x` `audit-x`）

## 5. 一つのスキルに一つの責務

「PDFとExcelとWordを扱うスキル」は分割する。責務が広いと description がぼやけ、
発動判定が不安定になる。

## 6. 検証

追加・変更したら必ず：

```bash
./scripts/validate.sh
```

そして実際に使ってみる。想定した場面で発動しなければ description を書き直す。
