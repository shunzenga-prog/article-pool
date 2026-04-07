#!/usr/bin/env python3
"""
🐱 小咪的公众号发布脚本
发布 Markdown 文章到微信公众号草稿箱

用法: python wechat_publish.py <文章路径> [标题]
"""

import requests
import json
import re
import os
import sys

# 从 .env 文件读取敏感信息
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()
APPID = os.getenv("WECHAT_APPID")
SECRET = os.getenv("WECHAT_SECRET")

def get_access_token():
    """获取 access_token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    resp = requests.get(url)
    data = resp.json()
    return data.get("access_token")

def upload_thumb(access_token, image_path):
    """上传封面图，获取 thumb_media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=thumb"
    
    with open(image_path, "rb") as f:
        files = {"media": f}
        resp = requests.post(url, files=files)
    
    data = resp.json()
    return data.get("media_id")

def markdown_to_html(md_content):
    """Markdown 转 HTML（支持公众号）"""
    html = md_content
    
    # 0. 先处理代码块（```...```）- 必须最先处理！
    # 使用占位符保护代码块
    code_blocks = []
    
    def save_code_block(match):
        lang = match.group(1) or ""
        code = match.group(2)
        
        # 转义 HTML 特殊字符
        code = code.replace('&', '&amp;')
        code = code.replace('<', '&lt;')
        code = code.replace('>', '&gt;')
        code = code.rstrip('\n')
        
        # 公众号支持的代码块样式
        code_html = f'''<pre style="background:#f6f8fa;padding:1em;border-radius:6px;overflow-x:auto;font-family:Menlo,Monaco,Consolas,'Courier New',monospace;font-size:14px;line-height:1.6;white-space:pre-wrap;word-wrap:break-word;"><code style="background:transparent;">{code}</code></pre>'''
        
        code_blocks.append(code_html)
        return f'__CODE_BLOCK_{len(code_blocks)-1}__'
    
    code_block_pattern = r'```(\w*)\n(.*?)```'
    html = re.sub(code_block_pattern, save_code_block, html, flags=re.DOTALL)
    
    # 0.5 处理行内代码（`code`）
    inline_code_pattern = r'`([^`]+)`'
    html = re.sub(inline_code_pattern, r'<code style="background:#f6f8fa;padding:2px 6px;border-radius:4px;font-family:Menlo,Monaco,Consolas,monospace;">\1</code>', html)
    
    # 1. 先处理表格（公众号需要 HTML 表格）
    # 匹配 markdown 表格
    table_pattern = r'\|(.+)\|\n\|[-:\| ]+\|\n((?:\|.+\|\n?)+)'
    
    def convert_table(match):
        header_line = match.group(1).strip()
        body_lines = match.group(2).strip().split('\n')
        
        # 解析表头
        headers = [cell.strip() for cell in header_line.split('|') if cell.strip()]
        
        # 解析表体
        rows = []
        for line in body_lines:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                rows.append(cells)
        
        # 构建 HTML 表格
        table_html = '<table style="width:100%;border-collapse:collapse;margin:1em 0;">'
        
        # 表头
        table_html += '<thead><tr>'
        for h in headers:
            table_html += f'<th style="border:1px solid #ddd;padding:8px;background:#f5f5f5;text-align:left;">{h}</th>'
        table_html += '</tr></thead>'
        
        # 表体
        table_html += '<tbody>'
        for row in rows:
            table_html += '<tr>'
            for cell in row:
                table_html += f'<td style="border:1px solid #ddd;padding:8px;">{cell}</td>'
            table_html += '</tr>'
        table_html += '</tbody></table>'
        
        return table_html
    
    html = re.sub(table_pattern, convert_table, html, flags=re.MULTILINE)
    
    # 2. 标题
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # 3. 加粗
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # 4. 斜体
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # 5. 引用
    html = re.sub(r'^> (.*?)$', r'<blockquote style="border-left:3px solid #ccc;padding-left:1em;color:#666;">\1</blockquote>', html, flags=re.MULTILINE)
    
    # 6. 换行处理
    # 6.1 先处理分隔线（--- 或 ***）- 在换行处理之前
    html = re.sub(r'\n---+\n', '\n<hr style="border:none;border-top:1px solid #eee;margin:2em 0;">\n', html)
    html = re.sub(r'\n\*\*\*+\n', '\n<hr style="border:none;border-top:1px solid #eee;margin:2em 0;">\n', html)
    
    # 6.2 处理独立行的分隔线
    html = re.sub(r'^---+$', '<hr style="border:none;border-top:1px solid #eee;margin:2em 0;">', html, flags=re.MULTILINE)
    html = re.sub(r'^\*\*\*+$', '<hr style="border:none;border-top:1px solid #eee;margin:2em 0;">', html, flags=re.MULTILINE)
    
    # 6.3 段落换行
    html = html.replace('\n\n', '</p><p>')
    html = html.replace('\n', '<br>')
    
    # 6.5 恢复代码块占位符
    for i, code_block in enumerate(code_blocks):
        html = html.replace(f'__CODE_BLOCK_{i}__', code_block)
    
    # 7. 包裹
    html = f"<section style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;\">{html}</section>"
    
    return html

def create_draft(access_token, title, content, thumb_media_id):
    """创建草稿"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    
    html_content = markdown_to_html(content)
    
    # 正确的格式（需要 thumb_media_id）
    data = {
        "articles": [{
            "title": title,
            "content": html_content,
            "thumb_media_id": thumb_media_id,
            "author": "小咪",
            "digest": "智能体元年、NVIDIA Blackwell、政策定调、市场数据"
        }]
    }
    
    # 关键：使用 ensure_ascii=False 避免中文被转成 unicode 编码
    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    
    # 必须指定 charset=utf-8，否则微信API会错误解析中文
    resp = requests.post(url, data=json_data, headers={'Content-Type': 'application/json; charset=utf-8'})
    return resp.json()

def get_article_cover(article_path):
    """根据文章内容智能生成封面图"""
    import subprocess
    
    article_dir = os.path.dirname(article_path)
    images_dir = os.path.join(article_dir, "images")
    article_cover = os.path.join(images_dir, "cover.jpg")
    
    # 删除旧封面，强制每次重新生成
    if os.path.exists(article_cover):
        os.remove(article_cover)
        print("🗑️ 已删除旧封面")
    
    # 生成新封面
    print("🎨 正在生成智能封面图...")
    script_dir = os.path.dirname(__file__)
    gen_script = os.path.join(script_dir, "generate-cover.py")
    
    if os.path.exists(gen_script):
        try:
            result = subprocess.run(
                ["python3", gen_script, article_path, "--output", article_cover],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0 and os.path.exists(article_cover):
                print(f"✅ 智能封面生成成功")
                return article_cover
            else:
                print(f"⚠️ 智能封面生成失败: {result.stderr}")
        except Exception as e:
            print(f"⚠️ 封面生成异常: {e}")
    
    # 降级方案：使用默认封面
    default_cover = os.path.join(script_dir, "default-cover.jpg")
    if os.path.exists(default_cover):
        print(f"⚠️ 使用默认封面: {default_cover}")
        return default_cover
    
    return None


def process_article_images(content, access_token):
    """处理文章配图"""
    import importlib.util
    
    script_dir = os.path.dirname(__file__)
    image_script = os.path.join(script_dir, "generate-article-images.py")
    
    if os.path.exists(image_script):
        # 动态导入配图模块
        spec = importlib.util.spec_from_file_location("image_gen", image_script)
        image_gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(image_gen)
        
        print("🎨 处理文章配图...")
        return image_gen.process_article_images(content, access_token)
    
    return content


def main():
    if len(sys.argv) < 2:
        print("用法: python wechat_publish.py <文章路径> [标题]")
        sys.exit(1)
    
    article_path = sys.argv[1]
    
    # 从文件名提取标题，或使用命令行参数
    if len(sys.argv) >= 3:
        title = sys.argv[2]
    else:
        # 从文章第一行提取标题
        with open(article_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            title = first_line.lstrip("# ").strip()
    
    # 读取文章
    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 获取 token
    token = get_access_token()
    if not token:
        print("❌ 获取 token 失败")
        sys.exit(1)
    print(f"✅ 获取 token 成功")
    
    # 🆕 处理文章配图
    content = process_article_images(content, token)
    
    # 智能生成封面图
    thumb_path = get_article_cover(article_path)
    
    thumb_media_id = ""
    if thumb_path and os.path.exists(thumb_path):
        thumb_media_id = upload_thumb(token, thumb_path)
        if thumb_media_id:
            print(f"✅ 封面图上传成功: {thumb_media_id}")
        else:
            print("⚠️ 封面图上传失败")
    else:
        print("⚠️ 无可用封面图，将使用默认样式")
    
    # 创建草稿
    print(f"📝 标题: {title} (长度: {len(title)})")
    result = create_draft(token, title, content, thumb_media_id)
    
    if "media_id" in result:
        print(f"✅ 草稿创建成功！")
        print(f"📝 草稿 ID: {result['media_id']}")
        print(f"👉 请登录公众号后台查看草稿箱")
    else:
        print(f"❌ 创建失败：{result}")

if __name__ == "__main__":
    main()