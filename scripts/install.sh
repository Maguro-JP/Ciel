#!/usr/bin/env bash
# スキルを使える場所へ置く。
#
#   install.sh                       置けるスキルの一覧を出す
#   install.sh <名前> ~/             自分の PC の全プロジェクトで使う
#   install.sh <名前> /path/to/repo  そのリポジトリで使う（コミットが要る）
#   install.sh --all <行き先>        全部置く
#   install.sh --sync <行き先>       毎週土曜に Ciel を取りに行く workflow を置く
#
# Claude Code が読むのは .claude/skills/ の下だけ。それ以外の場所に
# 置いても発動しない。~/.claude/ はその機械の中でしか効かないので、
# スマホや Web のセッションで使うならリポジトリに入れてコミットする。
set -euo pipefail
cd "$(dirname "$0")/.."
SRC=".claude/skills"

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

if [ "$1" = "--sync" ]; then
  [ $# -lt 2 ] && { echo "行き先を指定してください" >&2; exit 1; }
  dest="${2%/}"
  mkdir -p "$dest/.github/workflows"
  cp templates/ciel-sync.yml "$dest/.github/workflows/ciel-sync.yml"
  echo "置きました: $dest/.github/workflows/ciel-sync.yml"
  echo
  echo "コミットすると、毎週土曜 09:00（日本時間）に Ciel を見に行き、"
  echo "差分があるときだけ ciel-sync ブランチで PR を出します。"
  echo "共同開発者がいるリポジトリには置かないこと。"
  exit 0
fi

if [ "$1" = "--all" ]; then
  [ $# -lt 2 ] && { echo "行き先を指定してください" >&2; exit 1; }
  names=$(ls "$SRC")
  dest="$2"
else
  [ $# -lt 2 ] && { echo "行き先を指定してください" >&2; exit 1; }
  names="$1"
  dest="$2"
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
