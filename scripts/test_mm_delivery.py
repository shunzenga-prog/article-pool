import importlib.util
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))


def _load_delivery_module():
    spec = importlib.util.find_spec("validate_mm_delivery")
    assert spec is not None, "validate_mm_delivery module should exist"
    return importlib.import_module("validate_mm_delivery")


def _write_gradient(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = size
    rng = random.Random(width * 1_000_003 + height)
    block = max(18, min(width, height) // 18)
    raw = bytearray(width * height * 3)
    for y in range(height):
        for x in range(width):
            base = 42 if ((x // block) + (y // block)) % 2 == 0 else 214
            index = (y * width + x) * 3
            raw[index] = max(0, min(255, base + rng.randint(-28, 28)))
            raw[index + 1] = max(0, min(255, base + rng.randint(-18, 38)))
            raw[index + 2] = max(0, min(255, base + rng.randint(-38, 18)))
    img = Image.frombytes("RGB", size, bytes(raw))
    img.save(path, "PNG")


class MmDeliveryGateTests(unittest.TestCase):
    def test_delivery_gate_rejects_missing_cover_and_illustrations(self):
        validate_mm_delivery = _load_delivery_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            article = root / "文章" / "2026年05月" / "0527-Test.html"
            article.parent.mkdir(parents=True)
            article.write_text('<meta charset="UTF-8"><p><span>正文</span></p>', encoding="utf-8")

            report = validate_mm_delivery.validate_delivery(article, run_dir=root / "reports")

            self.assertFalse(report["passed"])
            check_ids = {check["id"] for check in report["checks"] if not check["passed"]}
            self.assertIn("illustrated_html.exists", check_ids)
            self.assertIn("cover.exists", check_ids)
            self.assertIn("body_images.present", check_ids)

    def test_delivery_gate_accepts_complete_delivery_with_quality_images(self):
        validate_mm_delivery = _load_delivery_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            article_dir = root / "文章" / "2026年05月"
            article = article_dir / "0527-Test.html"
            illustrated = article_dir / "0527-Test_illustrated.html"
            image_dir = article_dir / "images_test"
            cover = article_dir / "0527-Test.png"
            body_image = image_dir / "01-body.png"
            run_dir = root / "reports" / "mm-article" / "run"

            article_dir.mkdir(parents=True)
            run_dir.mkdir(parents=True)
            _write_gradient(cover, (1200, 675))
            _write_gradient(body_image, (670, 377))
            article.write_text('<meta charset="UTF-8"><p><span>正文</span></p>', encoding="utf-8")
            illustrated.write_text(
                '<meta charset="UTF-8"><p><span>正文</span></p>'
                '<table><tr><td><img src="images_test/01-body.png" alt="配图"></td></tr></table>',
                encoding="utf-8",
            )
            (run_dir / "image_requests.json").write_text('{"images":[]}', encoding="utf-8")
            (run_dir / "generated_images.json").write_text(
                json.dumps({"images": [{"id": "image_001", "path": str(body_image)}]}),
                encoding="utf-8",
            )
            for name, content in {
                "evidence.json": "{}",
                "title_decision.json": "{}",
                "content_prompt.md": "prompt",
                "visual_plan.json": "{}",
                "review.json": "{}",
                "publish_result.json": '{"status":"ready_not_published"}',
            }.items():
                (run_dir / name).write_text(content, encoding="utf-8")

            report = validate_mm_delivery.validate_delivery(article, run_dir=run_dir)

            self.assertTrue(report["passed"], report)
            by_id = {check["id"]: check for check in report["checks"]}
            self.assertTrue(by_id["cover.quality"]["passed"])
            self.assertTrue(by_id["body_images.quality"]["passed"])
            self.assertEqual(report["artifacts"]["cover"], str(cover))
            self.assertEqual(report["artifacts"]["illustrated_html"], str(illustrated))


if __name__ == "__main__":
    unittest.main()
