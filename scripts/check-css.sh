#!/usr/bin/env bash
# Check HTML files for WeChat-incompatible CSS patterns.
# Usage: bash scripts/check-css.sh [file|directory]
#   Exit 0 = clean, Exit 1 = violations found.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-$SCRIPT_DIR/../templates/}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

declare -A RULES=(
    ["linear-gradient"]="渐变背景（用实色 background 替代）"
    ["display:\\s*flex"]="Flex 布局（用 <table> 替代）"
    ["display:\\s*grid"]="Grid 布局（用 <table> 替代）"
    ["border-radius"]="圆角（微信不支持）"
    ["letter-spacing"]="字间距（微信会剥离）"
    ["font-style:\\s*italic"]="斜体（微信不支持）"
    ["text-transform"]="文本变换（微信会剥离）"
    ["opacity"]="透明度（用直接色值替代）"
    ["font-family"]="自定义字体（微信会剥离，保留默认即可）"
)

VIOLATIONS=0
FILES_CHECKED=0

echo "🔍 Checking WeChat CSS compatibility..."
echo "   Target: $TARGET"
echo "   Skipping: cover-previews/"
echo ""

while IFS= read -r -d '' file; do
    [[ "$file" != *.html ]] && continue
    # Skip cover-previews directory (browser previews, not for WeChat)
    [[ "$file" == *"/cover-previews/"* ]] && continue

    FILES_CHECKED=$((FILES_CHECKED + 1))
    FILE_VIOLATIONS=0

    for pattern in "${!RULES[@]}"; do
        matches=$(grep -ni "$pattern" "$file" 2>/dev/null | grep -v '^\s*[0-9]*:\s*<!--' | grep -v 'WeChat\|兼容\|已移除\|flex→table\|gradient→solid\|cover-previews' || true)
        if [ -n "$matches" ]; then
            if [ $FILE_VIOLATIONS -eq 0 ]; then
                echo -e "${RED}❌ $file${NC}"
            fi
            echo -e "   ${YELLOW}${RULES[$pattern]}${NC}"
            echo "$matches" | while IFS= read -r line; do
                echo "     $line"
            done
            FILE_VIOLATIONS=$((FILE_VIOLATIONS + 1))
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done

    if [ $FILE_VIOLATIONS -eq 0 ]; then
        echo -e "${GREEN}✅ $file${NC}"
    fi
done < <(find "$TARGET" -type f -name "*.html" -print0 2>/dev/null || true)

echo ""
echo "──────────────────────"
echo "Files checked: $FILES_CHECKED"
if [ $VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✅ All clear — no WeChat-incompatible CSS found.${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $VIOLATIONS violation(s) across checked files.${NC}"
    echo "   Fix the above patterns before publishing to WeChat."
    exit 1
fi
