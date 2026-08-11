#!/usr/bin/env bash
# 公開スキルを収集して corpus/ に置く（解析用。コミットはしない）
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p corpus && cd corpus

REPOS=(
  anthropics/skills
  obra/superpowers
  google/skills
  cloudflare/skills
  vercel-labs/skills
  phuryn/pm-skills
  coreyhaines31/marketingskills
)

for r in "${REPOS[@]}"; do
  n="${r//\//_}"
  if [ -d "$n" ]; then
    echo "skip $r (取得済み)"
    continue
  fi
  if git clone --depth 1 -q "https://github.com/$r.git" "$n" 2>/dev/null; then
    printf '%-34s %4s skills\n' "$r" "$(find "$n" -name SKILL.md | wc -l)"
  else
    printf '%-34s FAILED\n' "$r"
  fi
done

echo
echo "合計 $(find . -name SKILL.md | wc -l) skills"
