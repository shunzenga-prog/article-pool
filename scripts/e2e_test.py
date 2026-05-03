#!/usr/bin/env python3
"""
端到端集成测试：Markdown 文章 → 配图生成 → HTML 嵌入 → 质量验证
模拟完整的公众号文章开发流程
"""
import subprocess, sys, os, re, json

# ============================================================
# Step 1: 生成配图
# ============================================================
print("=" * 60)
print("Step 1: 运行 code_image_generator 生成配图")
print("=" * 60)

generator_path = "/sessions/dazzling-jolly-fermi/mnt/outputs/code_image_generator.py"
article_path = "/sessions/dazzling-jolly-fermi/mnt/outputs/test_article.md"
output_dir = "/sessions/dazzling-jolly-fermi/mnt/outputs/e2e_output"

os.makedirs(output_dir, exist_ok=True)
# 清理旧输出
for f in os.listdir(output_dir):
    os.remove(os.path.join(output_dir, f))

r = subprocess.run(
    ["python3", generator_path, "process", article_path,
     "-o", output_dir, "--execute", "--animate"],
    capture_output=True, text=True, timeout=45
)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:500])

# ============================================================
# Step 2: 质量验证
# ============================================================
print("\n" + "=" * 60)
print("Step 2: 图片质量验证")
print("=" * 60)

from PIL import Image

results = {"total": 0, "passed": 0, "failed": 0, "details": []}

for f in sorted(os.listdir(output_dir)):
    path = os.path.join(output_dir, f)
    size_kb = os.path.getsize(path) // 1024

    checks = []
    img_type = "unknown"

    if f.endswith(".png"):
        img = Image.open(path)
        w, h = img.size
        img_type = "png"

        # 验证项
        if w >= 500:
            checks.append(("宽度≥500px", True, f"{w}px"))
        else:
            checks.append(("宽度≥500px", False, f"{w}px (太窄)"))

        if h >= 100:
            checks.append(("高度≥100px", True, f"{h}px"))
        else:
            checks.append(("高度≥100px", False, f"{h}px (太矮)"))

        if size_kb >= 5:
            checks.append(("文件≥5KB", True, f"{size_kb}KB"))
        else:
            checks.append(("文件≥5KB", False, f"{size_kb}KB (太小)"))

        if size_kb <= 500:
            checks.append(("文件≤500KB", True, f"{size_kb}KB"))
        else:
            checks.append(("文件≤500KB", False, f"{size_kb}KB (可能过大)"))

    elif f.endswith(".gif"):
        import imageio
        frames = imageio.mimread(path)
        frame_count = len(frames)
        if len(frames[0].shape) == 3:
            h, w = frames[0].shape[:2]
        else:
            h, w = frames[0].shape[:2]

        img_type = "gif"

        checks.append(("帧数≥3", frame_count >= 3, f"{frame_count}帧"))
        checks.append(("宽度≥500px", w >= 500, f"{w}px"))
        checks.append(("文件≤500KB", size_kb <= 500, f"{size_kb}KB"))

    all_pass = all(c[1] for c in checks)
    results["total"] += 1
    if all_pass:
        results["passed"] += 1
    else:
        results["failed"] += 1

    status = "✅" if all_pass else "❌"
    print(f"\n  {status} {f} ({img_type}, {size_kb}KB)")
    for name, passed, detail in checks:
        print(f"     {'✓' if passed else '✗'} {name}: {detail}")

    results["details"].append({
        "file": f, "type": img_type, "size_kb": size_kb,
        "passed": all_pass, "checks": [(n, p, d) for n, p, d in checks]
    })

# ============================================================
# Step 3: HTML 嵌入模拟
# ============================================================
print("\n" + "=" * 60)
print("Step 3: HTML 嵌入模拟（生成带 img 标签的文章）")
print("=" * 60)

# 模拟：将 Markdown 中的代码块替换为 <img> 标签
with open(article_path, "r", encoding="utf-8") as f:
    md_content = f.read()

# 获取生成的图片列表
images = sorted([f for f in os.listdir(output_dir) if f.endswith(('.png', '.gif'))])

# 简单模拟：在文章末尾添加图片引用
html_parts = []
image_idx = 0

for line in md_content.split("\n"):
    html_parts.append(line)
    if line.startswith("```") and image_idx < len(images):
        img_file = images[image_idx]
        img_path = os.path.join(output_dir, img_file)
        size_kb = os.path.getsize(img_path) // 1024
        img_tag = f'<!-- 配图: {img_file} ({size_kb}KB) -->'
        img_tag += f'<img src="./images/{img_file}" alt="code screenshot" style="max-width:100%;border-radius:8px;" />'
        html_parts.append(img_tag)
        image_idx += 1

embed_html = "\n".join(html_parts)

html_path = os.path.join(output_dir, "embed_preview.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(embed_html)

print(f"  生成预览 HTML: {html_path}")
print(f"  嵌入图片数: {image_idx}")

# ============================================================
# Step 4: 总结报告
# ============================================================
print("\n" + "=" * 60)
print("📊 端到端测试报告")
print("=" * 60)
print(f"""
  总配图数: {results['total']}
  通过数:   {results['passed']}
  失败数:   {results['failed']}

  文件清单:
""")
for d in results["details"]:
    status = "✅" if d["passed"] else "❌"
    print(f"  {status} [{d['type'].upper()}] {d['file']} ({d['size_kb']}KB)")

# 保存 JSON 报告
report = {
    "article": article_path,
    "output_dir": output_dir,
    "results": results,
    "summary": f"{results['passed']}/{results['total']} images passed"
}
report_path = os.path.join(output_dir, "quality_report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n  质量报告: {report_path}")
print(f"\n{'✅ ALL TESTS PASSED' if results['failed'] == 0 else '❌ SOME TESTS FAILED'}")
