#!/usr/bin/env python3
"""
🐱 AI 图片生成工具
使用 pollinations.ai 免费生成图片
"""

import requests
from urllib.parse import quote
import os
import sys

def generate_image(prompt, output_path, width=1280, height=720, model="flux"):
    """
    生成 AI 图片
    
    Args:
        prompt: 图片描述
        output_path: 输出路径
        width: 宽度 (默认 1280)
        height: 高度 (默认 720)
        model: 模型 (flux, turbo)
    """
    # 使用正确的 API 端点
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
    params = {
        "width": width,
        "height": height,
        "model": model,
        "nologo": "true"
    }
    
    print(f"🎨 生成图片: {prompt[:50]}...")
    
    try:
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ 已保存: {output_path}")
        return True
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python ai-image-gen.py <prompt> <output_path> [width] [height]")
        print("示例: python ai-image-gen.py 'A futuristic AI robot' cover.png 1280 720")
        sys.exit(1)
    
    prompt = sys.argv[1]
    output_path = sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1280
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 720
    
    generate_image(prompt, output_path, width, height)

if __name__ == "__main__":
    main()