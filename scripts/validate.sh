#!/usr/bin/env bash
# Ciel skill validator — 構造チェックと秘密情報の簡易スキャン
set -uo pipefail

cd "$(dirname "$0")/.."

errors=0
warns=0
err()  { printf '  \033[31mERROR\033[0m  %s\n' "$1"; errors=$((errors+1)); }
warn() { printf '  \033[33mWARN \033[0m  %s\n' "$1"; warns=$((warns+1)); }

# ---- frontmatter の値を取り出す ----
front_value() {
  # $1: file, $2: key
  awk -v key="$2" '
    NR==1 && $0=="---" { inside=1; next }
    inside && $0=="---" { exit }
    inside {
      if (index($0, key ":") == 1) {
        sub("^" key ":[ \t]*", "")
        print
        exit
      }
    }
  ' "$1"
}

echo "== skills =="
shopt -s nullglob
dirs=(skills/*/)
if [ ${#dirs[@]} -eq 0 ]; then
  echo "  (スキルなし)"
fi

for dir in "${dirs[@]}"; do
  name="$(basename "$dir")"
  echo "- $name"

  file="$dir/SKILL.md"
  if [ ! -f "$file" ]; then
    err "$name: SKILL.md がない"
    continue
  fi

  if [ "$(head -n1 "$file")" != "---" ]; then
    err "$name: 1行目が '---' ではない（YAML frontmatter が必要）"
    continue
  fi

  fm_name="$(front_value "$file" name)"
  fm_desc="$(front_value "$file" description)"

  [ -n "$fm_name" ] || err "$name: frontmatter に name がない"
  [ -n "$fm_desc" ] || err "$name: frontmatter に description がない"

  if [ -n "$fm_name" ] && [ "$fm_name" != "$name" ]; then
    err "$name: name ('$fm_name') がディレクトリ名と一致しない"
  fi

  if ! printf '%s' "$name" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$'; then
    err "$name: ディレクトリ名は小文字・数字・ハイフンのみ"
  fi

  if [ -n "$fm_desc" ] && [ "${#fm_desc}" -lt 40 ]; then
    warn "$name: description が短い（${#fm_desc}文字）。発動条件を具体的に書く"
  fi

  lines=$(wc -l < "$file")
  if [ "$lines" -gt 500 ]; then
    warn "$name: SKILL.md が ${lines} 行。references/ に切り出すことを検討"
  fi

  for s in "$dir"scripts/*; do
    [ -f "$s" ] && [ ! -x "$s" ] && warn "$name: $s に実行権限がない"
  done
done

# ---- 秘密情報の簡易スキャン ----
echo
echo "== secret scan =="
patterns=(
  'sk-ant-[A-Za-z0-9_-]{20,}'
  'sk-[A-Za-z0-9]{32,}'
  'ghp_[A-Za-z0-9]{30,}'
  'gh[pousr]_[A-Za-z0-9]{30,}'
  'AKIA[0-9A-Z]{16}'
  'AIza[0-9A-Za-z_-]{30,}'
  'xox[baprs]-[A-Za-z0-9-]{10,}'
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
)
hit=0
for p in "${patterns[@]}"; do
  if out=$(grep -rInE --exclude-dir=.git --exclude=validate.sh "$p" . 2>/dev/null); then
    echo "$out" | while IFS= read -r l; do echo "  $l"; done
    hit=1
  fi
done
if [ "$hit" -eq 1 ]; then
  err "秘密情報らしき文字列を検出。コミット前に必ず取り除くこと"
else
  echo "  クリーン"
fi

if [ -f .env ]; then
  err ".env が存在する。コミットしないこと（.gitignore 済みか確認）"
fi

echo
echo "errors: $errors  warns: $warns"
[ "$errors" -eq 0 ]
