#!/usr/bin/env bash
# スキルを使える場所へ置く。
#
#   install.sh                       置けるスキルの一覧を出す
#   install.sh <名前> ~/             自分の PC の全プロジェクトで使う
#   install.sh <名前> /path/to/repo  そのリポジトリで使う（コミットが要る）
#   install.sh --all <行き先>        全部置く
#
# 定期的な配布は Raphael（private）の workflow が週1回まとめて行う。
# 各リポジトリに同期用の workflow は置かない。
#
# Claude Code が読むのは .claude/skills/ の下だけ。それ以外の場所に
# 置いても発動しない。~/.claude/ はその機械の中でしか効かないので、
# スマホや Web のセッションで使うならリポジトリに入れてコミットする。
set -euo pipefail
CALLER_PWD="$PWD"
cd "$(dirname "$0")/.."
SRC=".claude/skills"

# 行き先は呼び出し元の cwd を基準に解決する。ここで cd した後に
# 相対パスを使うと Ciel の中を指してしまう。
resolve() {
  case "$1" in
    /*|~*) printf '%s' "$1" ;;
    *)     printf '%s/%s' "$CALLER_PWD" "$1" ;;
  esac
}

list() {
  echo "置けるスキル:"
  for d in "$SRC"/*/; do
    n=$(basename "$d")
    desc=$(awk '/^description:/{sub(/^description:[ ]*/,""); sub(/。.*/,"。"); print; exit}' "$d/SKILL.md")
    printf "  %-18s %s\n" "$n" "$desc"
  done
  echo
  echo "使い方: $0 <名前> <行き先>    例: $0 ci-triage ~/"
}

[ $# -eq 0 ] && { list; exit 0; }

if [ "$1" = "--all" ]; then
  [ $# -lt 2 ] && { echo "行き先を指定してください" >&2; exit 1; }
  names=$(ls "$SRC")
  dest="$(resolve "$2")"
else
  [ $# -lt 2 ] && { echo "行き先を指定してください" >&2; exit 1; }
  names="$1"
  dest="$(resolve "$2")"
fi

target="${dest%/}/.claude/skills"
mkdir -p "$target"

for n in $names; do
  if [ ! -d "$SRC/$n" ]; then
    echo "そんなスキルはありません: $n" >&2
    exit 1
  fi
  rm -rf "${target:?}/$n"
  cp -r "$SRC/$n" "$target/$n"
  find "$target/$n" -name '*.py' -o -name '*.sh' | xargs -r chmod +x
  echo "置きました: $target/$n"
done

echo
case "$target" in
  "$HOME/.claude/skills")
    echo "この機械の全プロジェクトで使えます。"
    echo "スマホや Web のセッションには引き継がれません。" ;;
  *)
    echo "コミットすると、そのリポジトリでどの環境からでも使えます。"
    echo "  git -C ${dest%/} add .claude/skills && git -C ${dest%/} commit -m 'スキルを追加'" ;;
esac
