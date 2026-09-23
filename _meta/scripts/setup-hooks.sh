#!/bin/sh
#
# setup-hooks.sh — install git hooks from _meta/scripts/hooks/ into .git/hooks/
#
# Run this once after cloning the repo.
# Creates symlinks so hooks stay in sync with the committed versions.

set -e

# 本脚本位于 _meta/scripts/，仓库根需上溯两级
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK_SRC="$REPO_ROOT/_meta/scripts/hooks"
HOOK_DST="$REPO_ROOT/.git/hooks"

if [ ! -d "$HOOK_SRC" ]; then
    echo "ERROR: $HOOK_SRC not found" >&2
    exit 1
fi

mkdir -p "$HOOK_DST"

for hook in "$HOOK_SRC"/*; do
    name=$(basename "$hook")
    dst="$HOOK_DST/$name"
    # Remove any existing (file or symlink) before linking
    if [ -L "$dst" ] || [ -f "$dst" ]; then
        # Skip the auto-installed Qoder post-commit tracker (preserve it)
        if [ "$name" = "post-commit" ] && grep -q "Qoder AI tracker" "$dst" 2>/dev/null; then
            echo "  skip $name (Qoder tracker present)"
            continue
        fi
        rm "$dst"
    fi
    ln -s "$hook" "$dst"
    chmod +x "$hook"
    echo "  ✓ installed $name"
done

echo ""
echo "Hooks installed. 紧急情况下可用 git commit --no-verify 跳过（会留下 index.json 过期风险）。"
