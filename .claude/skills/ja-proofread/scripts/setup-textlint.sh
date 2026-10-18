#!/usr/bin/env bash
# textlint と日本語の規則集（ja-technical-writing、ja-spacing）をリポジトリの外に入れる。
# リポジトリに node_modules を増やさないため、置き場所は $CIEL_TEXTLINT_DIR か ~/.cache/ciel-textlint。
# proofread.py は、ここに textlint があれば自動で使う。無くても proofread.py は動く（正規表現だけになる）。
set -euo pipefail
dir="${CIEL_TEXTLINT_DIR:-$HOME/.cache/ciel-textlint}"
here="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$dir"
cd "$dir"
[ -f package.json ] || npm init -y >/dev/null
npm install --silent --no-audit --no-fund textlint textlint-rule-preset-ja-technical-writing textlint-rule-preset-ja-spacing
cp "$here/assets/textlintrc.json" "$dir/.textlintrc.json"
"$dir/node_modules/.bin/textlint" --version
echo "textlint を $dir に入れた。proofread.py が自動で使う。"
