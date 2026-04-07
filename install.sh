#!/bin/bash

# Article Pool 安装脚本
# 支持两种安装模式：standalone（独立）和 integrated（集成）

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
    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}  🐱 Article Pool 安装程序${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查 OpenClaw
check_openclaw() {
    if [ ! -d "$HOME/.openclaw" ]; then
        print_error "OpenClaw 未安装"
        echo ""
        echo "请先安装 OpenClaw: https://docs.openclaw.ai"
        exit 1
    fi
    print_step "OpenClaw 已安装"
}

# 独立模式安装（推荐）
install_standalone() {
    print_header
    echo -e "${GREEN}📦 独立模式安装${NC}"
    echo ""
    echo "Article Pool 将作为独立的创作目录使用"
    echo "Skills/Scripts 直接从本项目加载"
    echo ""
    
    check_openclaw
    
    # 创建必要的目录
    mkdir -p "$WORKSPACE_DIR/reports/materials"
    mkdir -p "$WORKSPACE_DIR/reports/images"
    
    # 复制配置模板
    if [ ! -f "$PROJECT_DIR/config/.env" ]; then
        cp "$PROJECT_DIR/config/.env.example" "$PROJECT_DIR/config/.env"
        print_warning "已创建配置模板: config/.env"
        echo "请编辑填入你的 API Keys"
    fi
    
    echo ""
    echo -e "${YELLOW}📝 需要手动配置 Agents:${NC}"
    echo ""
    echo "1. 打开 $PROJECT_DIR/agents/lobster-config.json"
    echo "2. 复制 agents.list 内容"
    echo "3. 编辑 $OPENCLAW_CONFIG"
    echo "4. 在 agents.list 中添加龙虾配置"
    echo "5. 将 workspace 路径改为: $PROJECT_DIR/agents/lobster-farm/<龙虾名>"
    echo ""
    echo "6. 重启 Gateway:"
    echo "   openclaw gateway restart"
    
    echo ""
    print_step "独立模式安装完成！"
    echo ""
    echo "下一步："
    echo "  1. 配置 API Keys: nano $PROJECT_DIR/config/.env"
    echo "  2. 配置 Agents: 参考 agents/lobster-config.json"
    echo "  3. 重启 Gateway: openclaw gateway restart"
}

# 集成模式安装（兼容现有 workspace）
install_integrated() {
    print_header
    echo -e "${GREEN}📦 集成模式安装${NC}"
    echo ""
    echo "Article Pool 将安装到现有 OpenClaw Workspace"
    echo ""
    
    check_openclaw
    
    # 使用 sync.sh 同步
    "$PROJECT_DIR/sync.sh" to-workspace
    
    # 复制配置模板
    if [ ! -f "$WORKSPACE_DIR/scripts/.env" ]; then
        cp "$PROJECT_DIR/config/.env.example" "$WORKSPACE_DIR/scripts/.env"
        print_warning "已创建配置模板"
    fi
    
    echo ""
    echo -e "${YELLOW}📝 需要手动配置 Agents:${NC}"
    echo "参考: $PROJECT_DIR/agents/lobster-config.json"
    
    echo ""
    print_step "集成模式安装完成！"
    echo ""
    echo "下一步："
    echo "  1. 配置 API Keys: nano $WORKSPACE_DIR/scripts/.env"
    echo "  2. 配置 Agents: 参考 agents/lobster-config.json"
    echo "  3. 重启 Gateway: openclaw gateway restart"
}

# 显示帮助
show_help() {
    print_header
    echo "用法:"
    echo "  $0 [模式]"
    echo ""
    echo "模式:"
    echo "  standalone    独立模式（推荐）- Article Pool 作为独立目录"
    echo "  integrated    集成模式 - 安装到现有 Workspace"
    echo "  help          显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 standalone"
    echo "  $0 integrated"
}

# 主函数
main() {
    MODE=${1:-"standalone"}
    
    case "$MODE" in
        "standalone")
            install_standalone
            ;;
        "integrated")
            install_integrated
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "未知模式: $MODE"
            show_help
            exit 1
            ;;
    esac
}

main "$@"