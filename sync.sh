#!/bin/bash

# Article Pool 智能同步脚本
# 使用 rsync 自动同步整个目录，新增文件自动包含

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="$HOME/.openclaw/workspace"
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Article Pool 同步工具${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示当前状态
show_status() {
    print_header
    echo "📊 当前状态:"
    echo ""
    
    echo "Article Pool 目录: $PROJECT_DIR"
    echo "  - Skills: $(find "$PROJECT_DIR/skills" -type f -name '*.md' 2>/dev/null | wc -l) 个"
    echo "  - Scripts: $(find "$PROJECT_DIR/scripts" -type f -name '*.py' 2>/dev/null | wc -l) 个"
    echo "  - Templates: $(find "$PROJECT_DIR/templates" -type f 2>/dev/null | wc -l) 个"
    echo ""
    
    echo "OpenClaw Workspace: $WORKSPACE_DIR"
    echo "  - Skills: $(find "$WORKSPACE_DIR/skills" -type f -name '*.md' 2>/dev/null | wc -l) 个"
    echo "  - Scripts: $(find "$WORKSPACE_DIR/scripts" -type f -name '*.py' 2>/dev/null | wc -l) 个"
    echo ""
    
    echo "Git 状态:"
    cd "$PROJECT_DIR"
    git status -s 2>/dev/null || echo "  (不在 Git 仓库中)"
}

# 同步到 Workspace（从项目同步到 OpenClaw）
sync_to_workspace() {
    print_header
    echo -e "${GREEN}🔄 从 Article Pool 同步到 OpenClaw Workspace...${NC}"
    echo ""
    
    # 创建必要的目录
    mkdir -p "$WORKSPACE_DIR/skills"
    mkdir -p "$WORKSPACE_DIR/scripts"
    mkdir -p "$WORKSPACE_DIR/templates"
    
    # 同步 skills（整个目录，自动包含新增）
    echo "📦 同步 Skills..."
    rsync -av --delete "$PROJECT_DIR/skills/" "$WORKSPACE_DIR/skills/"
    print_status "Skills 已同步 ($(ls "$PROJECT_DIR/skills" | wc -l) 个)"
    
    # 同步 scripts（整个目录，自动包含新增）
    echo "📦 同步 Scripts..."
    rsync -av --delete "$PROJECT_DIR/scripts/" "$WORKSPACE_DIR/scripts/"
    chmod +x "$WORKSPACE_DIR/scripts/*.py" 2>/dev/null
    print_status "Scripts 已同步 ($(ls "$PROJECT_DIR/scripts/*.py" 2>/dev/null | wc -l) 个)"
    
    # 同步 templates
    echo "📦 同步 Templates..."
    rsync -av "$PROJECT_DIR/templates/" "$WORKSPACE_DIR/templates/"
    print_status "Templates 已同步"
    
    # 同步 agents 配置提示
    echo ""
    echo -e "${YELLOW}⚠️  Agents 配置需要手动合并:${NC}"
    echo "  1. 打开 $PROJECT_DIR/agents/lobster-config.json"
    echo "  2. 复制 agents.list 到 $OPENCLAW_CONFIG"
    echo "  3. 运行: openclaw gateway restart"
    
    echo ""
    print_status "同步完成！"
}

# 同步到项目（从 OpenClaw 同步回项目）
sync_from_workspace() {
    print_header
    echo -e "${GREEN}🔄 从 OpenClaw Workspace 同步到 Article Pool...${NC}"
    echo ""
    
    # 同步 skills
    echo "📦 同步 Skills..."
    rsync -av --delete "$WORKSPACE_DIR/skills/" "$PROJECT_DIR/skills/"
    print_status "Skills 已同步"
    
    # 同步 scripts
    echo "📦 同步 Scripts..."
    rsync -av --delete "$WORKSPACE_DIR/scripts/" "$PROJECT_DIR/scripts/"
    print_status "Scripts 已同步"
    
    # 同步 templates
    echo "📦 同步 Templates..."
    rsync -av "$WORKSPACE_DIR/templates/" "$PROJECT_DIR/templates/"
    print_status "Templates 已同步"
    
    echo ""
    echo -e "${YELLOW}📝 建议执行:${NC}"
    echo "  git add . && git commit -m 'sync from workspace' && git push"
    
    echo ""
    print_status "同步完成！"
}

# 主函数
main() {
    MODE=${1:-"status"}
    
    case "$MODE" in
        "status"|"--status"|"-s")
            show_status
            ;;
        "to-workspace"|"--to"|"-t")
            sync_to_workspace
            ;;
        "from-workspace"|"--from"|"-f")
            sync_from_workspace
            ;;
        "help"|"--help"|"-h")
            print_header
            echo "用法:"
            echo "  $0 [命令]"
            echo ""
            echo "命令:"
            echo "  status, -s     显示当前状态（默认）"
            echo "  to, -t         从项目同步到 OpenClaw Workspace"
            echo "  from, -f       从 Workspace 同步回项目"
            echo "  help, -h       显示帮助"
            ;;
        *)
            print_error "未知命令: $MODE"
            echo "运行 $0 help 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"