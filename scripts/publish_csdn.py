#!/usr/bin/env python3
"""
CSDN 文章发布脚本 — Playwright 浏览器自动化方案
将 Markdown 文章通过 CSDN 编辑器发布。

用法: python publish_csdn.py <文章.md> [--tags 标签] [--headless] [--publish]

首次运行会打开浏览器让你登录 CSDN，登录状态自动保存，
后续运行无需再次登录。不需要配置任何 Cookie 或 nsId。

CSDN 创作请直接写 Markdown 文件。跨平台迁移用 AI 重写，禁止机械转换。
"""

import json
import os
import sys
import argparse
import re
import time

try:
    from preferences import get_prefs as _get_prefs
    _pub_prefs = _get_prefs()
except Exception:
    _pub_prefs = {}

from paths import PROJECT_ROOT, REPORTS_DIR


# Playwright persistent profile directory
PROFILE_DIR = PROJECT_ROOT / "config" / "csdn_profile"

# CSDN blank editor — not_checkout=1 creates a new article every time
EDITOR_URL = "https://editor.csdn.net/md?not_checkout=1"


def ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        print("❌ 需要安装 Playwright:")
        print("   pip install playwright")
        print("   playwright install chromium")
        sys.exit(1)


def log_publish(title, url, author, tags=None):
    from datetime import datetime
    from paths import CSDN_PUBLISH_LOG_FILE as log_file

    log = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
        except (json.JSONDecodeError, ValueError):
            log = []

    entry = {
        "title": title,
        "url": url,
        "author": author,
        "published_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "status": "published",
        "platform": "csdn",
    }
    if tags:
        entry["tags"] = tags

    log.append(entry)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"\n📋 已记录到 CSDN 发布日志: {log_file}")


def extract_title_from_md(md_content):
    """Extract title from Markdown. Tries # heading first, then first meaningful line."""
    # Try # heading
    match = re.search(r'^#\s+(.+)', md_content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    # Fallback: look through lines for the real title
    # Skip short section labels and metadata, find the actual title line
    skip_patterns = [
        r'^(AI|TECH|DEEP|MORNING|NEWS|SIGNALS|TUTORIAL)\b',  # section labels
        r'^\d{4}\.\d{2}\.\d{2}',       # date lines
        r'^.*·\s*(阅读|分钟|系列|共\d)',   # metadata
        r'^.{1,8}$',                     # very short lines (labels)
    ]
    for line in md_content.split('\n'):
        stripped = line.strip()
        if not stripped or stripped in ('---', '···', '—', '>'):
            continue
        # Remove leading > if it's a blockquote
        text = re.sub(r'^>\s*', '', stripped)
        # Skip if matches any skip pattern
        if any(re.match(p, text) for p in skip_patterns):
            continue
        # Found a reasonable title candidate (long enough, not metadata)
        if len(text) > 10:
            return text
    return None


def is_logged_in(page):
    """Check if user is logged into CSDN."""
    try:
        # On any CSDN page: look for user avatar/menu or login button
        # Logged in → has user avatar or menu; Not logged in → has "登录" button
        login_btn = page.locator('text=登录').first
        if login_btn.count() > 0:
            try:
                if login_btn.is_visible(timeout=1000):
                    return False
            except Exception:
                pass
        return True
    except Exception:
        return True  # assume logged in if can't determine


def wait_for_login(page):
    """Wait for user to complete manual login in the browser window."""
    print("\n⏳ 请在浏览器中登录 CSDN...")
    print("   （支持微信扫码 / 账号密码 / 短信验证码）")

    # CSDN may redirect to login page
    max_wait = 180  # 3 minutes
    interval = 2
    elapsed = 0

    while elapsed < max_wait:
        if is_logged_in(page):
            print("✅ 登录成功！")
            return True

        # Check if we're on a login page
        current_url = page.url
        if "passport.csdn.net" in current_url or "login" in current_url.lower():
            dots = "." * ((elapsed // 5) % 4 + 1)
            print(f"\r   等待登录{dots}   ", end="", flush=True)

        time.sleep(interval)
        elapsed += interval

    print("\n❌ 登录超时（3 分钟）")
    return False


def fill_editor_content(page, md_content):
    """Fill the CSDN Markdown editor with content.

    Strategy (tried in order):
    1. JS injection via contenteditable/CodeMirror (most reliable — not blocked by modals)
    2. Playwright clipboard API + Ctrl+V paste (fallback)
    """
    # Strategy 1: JS injection (not blocked by modals)
    if _inject_via_javascript(page, md_content):
        return

    # Strategy 2: Clipboard paste (may be blocked by modals)
    if _paste_via_playwright_clipboard(page, md_content):
        return

    print("⚠️  所有填入方式均失败，内容可能未填入编辑器")


def _paste_via_playwright_clipboard(page, md_content):
    """Use Playwright's clipboard API to set content and paste into editor."""
    try:
        # Grant clipboard permissions to the page
        page.context.grant_permissions(["clipboard-read", "clipboard-write"])

        # Use navigator.clipboard.writeText to set clipboard
        page.evaluate("text => navigator.clipboard.writeText(text)", md_content)
        # Wait for the async clipboard write to complete
        page.wait_for_timeout(300)

        # Focus the editor area and paste
        editor_area = page.locator('.cledit-section').first
        if editor_area.count() == 0:
            editor_area = page.locator('.editor').first
        editor_area.click()
        page.wait_for_timeout(200)

        # Select all existing content and replace with paste
        page.keyboard.press("Control+a")
        page.wait_for_timeout(100)
        page.keyboard.press("Control+v")
        page.wait_for_timeout(500)

        print("✅ 内容已填入编辑器（剪贴板方式）")
        return True
    except Exception as e:
        print(f"   Playwright 剪贴板方式失败: {e}")
        return False


def _inject_via_javascript(page, md_content):
    """Inject content via CodeMirror or Monaco editor API."""
    js_code = """
    (content) => {
        // CodeMirror 5
        const cmEl = document.querySelector('.CodeMirror');
        if (cmEl && cmEl.CodeMirror) {
            cmEl.CodeMirror.setValue(content);
            return 'codemirror5';
        }
        // CodeMirror 6
        const cmView = document.querySelector('.cm-editor');
        if (cmView && cmView.cmView && cmView.cmView.view) {
            const view = cmView.cmView.view;
            view.dispatch({
                changes: {from: 0, to: view.state.doc.length, insert: content}
            });
            return 'codemirror6';
        }
        // Monaco
        if (typeof monaco !== 'undefined') {
            const editors = monaco.editor.getEditors();
            if (editors.length > 0) {
                editors[0].setValue(content);
                return 'monaco';
            }
        }
        // contenteditable fallback
        const editable = document.querySelector('[contenteditable="true"]');
        if (editable) {
            editable.textContent = content;
            editable.dispatchEvent(new Event('input', {bubbles: true}));
            return 'contenteditable';
        }
        return null;
    }
    """
    try:
        result = page.evaluate(js_code, md_content)
        if result:
            print(f"✅ 内容已填入编辑器（{result}）")
            return True
        print(f"   未识别到编辑器类型")
        return False
    except Exception as e:
        print(f"   JS 注入失败: {e}")
        return False


def add_tags(page, tags):
    """Add tags to the article."""
    if not tags:
        return

    try:
        # CSDN's tag UI — find the tag input area in the article settings bar
        # The tag bar is usually below the editor, with a "标签" label and input
        tag_input_selectors = [
            'input[placeholder*="标签"]',
            'input[placeholder*="搜索"]',
            'div[class*="tag"] input[type="text"]',
            '.mark_selection_box input',
            'input[class*="tag"]',
        ]

        for tag in tags:
            added = False
            for input_sel in tag_input_selectors:
                try:
                    tag_input = page.locator(input_sel).first
                    if tag_input.count() > 0 and tag_input.is_visible(timeout=1000):
                        tag_input.click(timeout=2000)
                        tag_input.fill(tag)
                        page.wait_for_timeout(1500)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(500)
                        print(f"   🏷️  标签已添加: {tag}")
                        added = True
                        break
                except Exception:
                    continue

            if not added:
                print(f"   ⚠️  无法添加标签: {tag}")
                break

        # Close any open tag panel
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    except Exception as e:
        print(f"⚠️  添加标签时出错: {e}（已跳过）")


def _click_save_draft(page):
    """Click CSDN's '保存草稿' button to explicitly save the article."""
    save_selectors = [
        'button:has-text("保存草稿")',
        'text=保存草稿',
        'button:has-text("保存")',
        '[class*="save"]',
        '[class*="draft"]',
    ]
    for selector in save_selectors:
        try:
            btn = page.locator(selector).first
            if btn.count() > 0 and btn.is_visible(timeout=2000):
                btn.click()
                page.wait_for_timeout(2000)
                print(f"✅ 已保存草稿")
                return True
        except Exception:
            continue

    print("⚠️  未找到「保存草稿」按钮，依赖自动保存")


def dismiss_modals(page):
    """Dismiss any CSDN popup modals (template chooser, announcements, etc.)."""
    # Always try Escape first for CSDN modals (most reliable)
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    except Exception:
        pass

    # Then try clicking specific close buttons
    dismiss_selectors = [
        'button:has-text("跳过")',
        'button:has-text("关闭")',
        'button:has-text("取消")',
        'div[class*="modal"] button:has-text("跳过")',
        'div[class*="modal"] button:has-text("关闭")',
        'div[class*="modal"] .close',
        'div[class*="modal"] [class*="close"]',
        '.modal_outer button[class*="close"]',
        'button[aria-label="关闭"]',
    ]
    for selector in dismiss_selectors:
        try:
            btn = page.locator(selector).first
            if btn.count() > 0 and btn.is_visible(timeout=1000):
                btn.click()
                page.wait_for_timeout(500)
                print(f"✅ 已关闭弹窗")
                return
        except Exception:
            continue


def click_publish(page):
    """Click the publish button and wait for result.

    CSDN has a two-step publish flow:
    1. Click "发布文章" button → opens publish settings panel
    2. In the panel, click "确定" to confirm publish
    """
    try:
        # Dismiss any modals first
        dismiss_modals(page)

        # Step 1: Click "发布文章" button
        publish_btn = page.locator('button:has-text("发布文章")').first
        if publish_btn.count() == 0:
            publish_btn = page.locator('[class*="btn-publish"]').first

        if publish_btn.count() == 0 or not publish_btn.is_visible(timeout=3000):
            print("❌ 未找到发布按钮")
            return None

        publish_btn.click()
        print("📤 已点击发布按钮...")
        page.wait_for_timeout(2000)

        # Step 2: Handle the publish settings panel
        page.wait_for_timeout(1000)

        # Look for the confirm/publish button
        confirm_selectors = [
            'button:has-text("确定并发布")',
            'button:has-text("确认发布")',
            'button:has-text("发布")',
            'button:has-text("确定")',
            'div[class*="modal"] button:has-text("确定")',
            'div[class*="publish"] button:has-text("发布")',
        ]
        for selector in confirm_selectors:
            try:
                confirm_btn = page.locator(selector).first
                if confirm_btn.count() > 0 and confirm_btn.is_visible(timeout=2000):
                    confirm_btn.click()
                    print("📤 已确认发布...")
                    page.wait_for_timeout(3000)
                    break
            except Exception:
                continue

        # Check result
        current_url = page.url
        if "/details/" in current_url or "blog.csdn.net" in current_url:
            return current_url

        # Check for success toast
        success_texts = ["发布成功", "文章已发布"]
        for text in success_texts:
            try:
                if page.locator(f'text={text}').first.is_visible(timeout=1000):
                    return current_url
            except Exception:
                continue

        return current_url if "blog.csdn.net" in current_url else None

    except Exception as e:
        print(f"❌ 点击发布时出错: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="发布 Markdown 文章到 CSDN（Playwright 浏览器自动化）")
    parser.add_argument("article", help="Markdown 文章文件路径（.md）")
    parser.add_argument("title", nargs="?", default=None, help="文章标题（默认从 # 标题提取）")
    parser.add_argument("--tags", default="", help="标签，逗号分隔（如 AI,Python,开源）")
    parser.add_argument("--author", default=_pub_prefs.get('author', {}).get('name', '小咪'),
                        help="作者名")
    parser.add_argument("--headless", action="store_true", help="无头模式（不显示浏览器窗口）")
    parser.add_argument("--publish", action="store_true",
                        help="自动发布（默认只填充到编辑器，需人工确认后手动点击发布）")
    args = parser.parse_args()

    # Validate file
    if not os.path.exists(args.article):
        print(f"❌ 文件不存在: {args.article}")
        sys.exit(1)

    with open(args.article, "r", encoding="utf-8") as f:
        md_body = f.read()

    title = args.title or extract_title_from_md(md_body)
    if not title:
        print("❌ 无法提取标题（MD 文件需以 # 标题开头），请通过命令行参数指定")
        sys.exit(1)

    # Parse tags
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    print(f"\n📝 正在填充 CSDN 编辑器{'（自动发布模式）' if args.publish else ''}...")
    print(f"   文件: {args.article}")
    print(f"   标题: {title}")
    print(f"   标签: {tags or '（无）'}")
    print(f"   内容: {len(md_body)} 字符")

    # Launch Playwright
    sync_playwright = ensure_playwright()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=args.headless,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )
        page = context.new_page()

        try:
            # Navigate to blank editor (not_checkout=1 = new article)
            print(f"\n🌐 正在打开 CSDN 编辑器...")
            page.goto(EDITOR_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            # Check login state
            if not is_logged_in(page):
                print("⚠️  尚未登录 CSDN")
                if args.headless:
                    print("❌ 无头模式下无法登录，请先不带 --headless 运行一次登录")
                    sys.exit(1)
                if not wait_for_login(page):
                    sys.exit(1)
                page.goto(EDITOR_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
            else:
                print("✅ 已登录 CSDN")

            # Dismiss any template chooser / announcement modals
            page.wait_for_timeout(1000)
            dismiss_modals(page)
            page.wait_for_timeout(500)

            # Fill title
            print(f"\n📝 正在填写标题...")
            title_input = page.locator('input[placeholder*="文章标题"]')
            if title_input.count() > 0:
                title_input.first.fill("")
                title_input.first.fill(title)
                print(f"✅ 标题已填写")
            else:
                print("⚠️  未找到标题输入框")

            # Fill content
            print(f"\n📄 正在填入文章内容 ({len(md_body)} 字符)...")
            fill_editor_content(page, md_body)
            page.wait_for_timeout(1000)

            # Click "保存草稿" to explicitly save
            _click_save_draft(page)
            page.wait_for_timeout(2000)

            # Add tags
            if tags:
                print(f"\n🏷️  正在添加标签...")
                add_tags(page, tags)

            if args.publish:
                # Auto-publish: click through the publish flow
                print(f"\n🚀 正在自动发布...")
                result_url = click_publish(page)

                if result_url:
                    print(f"\n{'='*50}")
                    print(f"✅ CSDN 发布成功！")
                    print(f"🔗 {result_url}")
                    print(f"{'='*50}")
                    log_publish(title, result_url, args.author, tags)
                else:
                    print(f"\n⚠️  自动发布未确认，请检查浏览器窗口手动完成")
                    print(f"   当前页面: {page.url}")
            else:
                # Default: fill only, human confirms
                print(f"\n{'='*50}")
                print(f"✅ 内容已填入 CSDN 编辑器")
                print(f"📄 来源: {args.article}")
                print(f"📝 标题: {title}")
                print(f"🏷️  标签: {tags or '（无）'}")
                print(f"💡 请在浏览器中检查内容，确认无误后手动点击「发布文章」")
                print(f"   如需自动发布，使用 --publish 参数")
                print(f"{'='*50}")

                # Check if articleId is in URL (confirms draft was saved)
                page.wait_for_timeout(2000)
                if 'articleId=' in page.url:
                    print(f"✅ 草稿已保存: {page.url}")
                else:
                    print(f"💡 请确认草稿已保存（点击「保存草稿」按钮）")

        except Exception as e:
            print(f"\n❌ 发布过程出错: {e}")
            print(f"   浏览器窗口已保留，请手动检查状态")
            print(f"   当前页面: {page.url}")
            sys.exit(1)
        finally:
            context.close()


if __name__ == "__main__":
    main()
