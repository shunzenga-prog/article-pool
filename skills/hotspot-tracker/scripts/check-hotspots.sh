#!/bin/bash
# AI热点追踪脚本
# 使用 DuckDuckGo HTML 搜索（避开 API 限制）

echo "=== AI热点追踪 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M')"
echo ""

# 使用 curl 搜索 DuckDuckGo HTML
echo "1. 今日AI热点..."
curl -s "https://html.duckduckgo.com/html/?q=AI+热点+今天" | grep -oP 'class="result__a"[^>]*>[^<]*' | head -5 | sed 's/class="result__a"[^>]*>/  /'

echo ""
echo "2. AI新闻最新..."
curl -s "https://html.duckduckgo.com/html/?q=人工智能+新闻+最新" | grep -oP 'class="result__a"[^>]*>[^<]*' | head -5 | sed 's/class="result__a"[^>]*>/  /'

echo ""
echo "3. 大模型动态..."
curl -s "https://html.duckduckgo.com/html/?q=大模型+动态+2026" | grep -oP 'class="result__a"[^>]*>[^<]*' | head -5 | sed 's/class="result__a"[^>]*>/  /'

echo ""
echo "=== 追踪完成 ==="