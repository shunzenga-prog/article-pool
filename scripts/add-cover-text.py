#!/usr/bin/env python3
"""
🐱 封面图添加文字脚本
在图片上叠加标题和 logo（支持中文、自动换行）
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys

def wrap_text(text, max_width, font):
    """智能换行 - 英文按词分，中文按字符分"""
    import re
    
    # 分割为英文单词和中文字符
    tokens = re.findall(r'[a-zA-Z]+|[^a-zA-Z\s]', text)
    
    lines = []
    current_line = ""
    
    for token in tokens:
        test_line = current_line + token
        # 用临时图片计算宽度
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = token
    
    if current_line:
        lines.append(current_line)
    
    return lines

def calculate_font_size(title, width, min_margin=20, min_font_size=32, max_font_size=64):
    """
    根据标题长度自动计算字号
    
    Args:
        title: 标题文本
        width: 图片宽度
        min_margin: 最小边距（默认 20px）
        min_font_size: 最小字号（默认 32px）
        max_font_size: 最大字号（默认 64px）
    
    Returns:
        最佳字号
    """
    # 可用宽度 = 图片宽度 - 2 * 最小边距
    max_text_width = width - 2 * min_margin
    
    # 从最大字号开始尝试
    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    
    for font_size in range(max_font_size, min_font_size - 1, -2):  # 每次减 2px
        try:
            font = ImageFont.truetype(font_path, font_size)
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            
            # 如果文字宽度 <= 可用宽度，返回此字号
            if text_width <= max_text_width:
                # 计算实际边距
                actual_margin = (width - text_width) // 2
                print(f"📏 字号: {font_size}px, 实际边距: {actual_margin}px (最小: {min_margin}px)")
                return font_size
        except:
            continue
    
    # 如果所有字号都太大，返回最小字号
    print(f"⚠️ 标题过长，使用最小字号: {min_font_size}px")
    return min_font_size

def add_text_to_cover(image_path, output_path, title, subtitle=None, logo_path=None):
    """
    在封面图上添加文字
    
    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径
        title: 主标题
        subtitle: 副标题（可选）
        logo_path: Logo 路径（可选）
    """
    # 打开图片
    img = Image.open(image_path)
    
    # 如果是 RGBA，转换为 RGB（白色背景）
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # 加载中文字体
    try:
        # 优先使用中文字体
        font_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Noto Sans CJK SC
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",           # 文泉驿微米黑
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",     # Noto Serif CJK SC Bold
        ]
        
        title_font = None
        sub_font = None
        
        # 自动计算主标题字号
        title_font_size = calculate_font_size(title, width, min_margin=20)
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                print(f"✅ 使用字体: {font_path}")
                title_font = ImageFont.truetype(font_path, title_font_size)  # 动态字号
                sub_font = ImageFont.truetype(font_path, int(title_font_size * 2 / 3))  # 副标题 = 主标题的 2/3
                break
        
        if title_font is None:
            print("⚠️ 未找到中文字体，使用默认字体")
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()
            
    except Exception as e:
        print(f"⚠️ 字体加载失败: {e}")
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
    
    # 自动换行主标题
    max_text_width = width - 40  # 左右各留 20px 边距（更紧凑）
    title_lines = wrap_text(title, max_text_width, title_font)
    
    print(f"📝 标题分行: {title_lines}")
    
    # 计算总高度
    line_height = 65  # 每行高度
    total_title_height = len(title_lines) * line_height
    
    # 起始 Y 位置（居中偏上）
    start_y = height // 2 - total_title_height // 2 - 20
    
    # 绘制每一行
    for i, line in enumerate(title_lines):
        # 计算行宽度
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        line_bbox = temp_draw.textbbox((0, 0), line, font=title_font)
        line_width = line_bbox[2] - line_bbox[0]
        
        line_x = (width - line_width) // 2
        line_y = start_y + i * line_height
        
        # 绘制阴影效果
        shadow_offset = 3
        draw.text((line_x + shadow_offset, line_y + shadow_offset), line, font=title_font, fill=(0, 0, 0, 150))
        
        # 绘制白色主标题
        draw.text((line_x, line_y), line, font=title_font, fill=(255, 255, 255))
    
    # 绘制副标题（如果有）
    if subtitle:
        # 自动换行副标题
        sub_lines = wrap_text(subtitle, max_text_width, sub_font)
        
        sub_start_y = start_y + total_title_height + 25
        
        for i, line in enumerate(sub_lines):
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            line_bbox = temp_draw.textbbox((0, 0), line, font=sub_font)
            line_width = line_bbox[2] - line_bbox[0]
            
            line_x = (width - line_width) // 2
            line_y = sub_start_y + i * 35
            
            draw.text((line_x, line_y), line, font=sub_font, fill=(200, 200, 200))
    
    # 添加 Logo（如果有）
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path)
        # 缩放 Logo
        logo_size = 80
        logo = logo.resize((logo_size, logo_size))
        
        # 右下角位置
        logo_x = width - logo_size - 20
        logo_y = height - logo_size - 20
        
        # 如果 Logo 有透明度，需要处理
        if logo.mode == 'RGBA':
            img.paste(logo, (logo_x, logo_y), mask=logo.split()[3])
        else:
            img.paste(logo, (logo_x, logo_y))
    
    # 保存
    img.save(output_path, 'PNG')
    print(f"✅ 已保存: {output_path}")

def main():
    if len(sys.argv) < 4:
        print("用法: python add-cover-text.py <输入图片> <输出图片> <标题> [副标题]")
        print("示例: python add-cover-text.py cover.png output.png 'Anthropic调整OpenClaw付费政策' '50倍成本上涨怎么办'")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_path = sys.argv[2]
    title = sys.argv[3]
    subtitle = sys.argv[4] if len(sys.argv) > 4 else None
    
    add_text_to_cover(image_path, output_path, title, subtitle)

if __name__ == "__main__":
    main()