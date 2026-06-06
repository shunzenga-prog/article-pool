import json
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import illustration_gen


class IllustrationStrategyTests(unittest.TestCase):
    def test_legacy_strategy_removes_agent_generate_source(self):
        sources = {
            "agent_generate": {"enabled": True, "priority": 1},
            "og_image": {"enabled": True, "priority": 2},
            "fallback_pattern": {"enabled": True, "priority": 9},
        }

        ordered = illustration_gen.get_ordered_source_configs(sources, "legacy")

        self.assertEqual([name for name, _ in ordered], ["og_image", "fallback_pattern"])

    def test_agent_first_strategy_promotes_agent_generate_source(self):
        sources = {
            "og_image": {"enabled": True, "priority": 1},
            "agent_generate": {"enabled": True, "priority": 9},
            "fallback_pattern": {"enabled": True, "priority": 10},
        }

        ordered = illustration_gen.get_ordered_source_configs(sources, "agent_first")

        self.assertEqual([name for name, _ in ordered][:2], ["agent_generate", "og_image"])

    def test_local_agent_manifest_ignores_missing_images(self):
        tmp_path = SCRIPTS / self._testMethodName
        tmp_path.mkdir(exist_ok=True)
        self.addCleanup(lambda: self._remove_tree(tmp_path))
        image_path = (tmp_path / "generated.png").resolve()
        image_path.write_bytes(b"fake-image")
        missing_path = (tmp_path / "missing.png").resolve()
        manifest_path = tmp_path / "generated_images.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "images": [
                        {"id": "image_001", "path": str(image_path)},
                        {"id": "image_002", "path": str(missing_path)},
                    ]
                }
            ),
            encoding="utf-8",
        )

        images = illustration_gen.load_agent_image_manifest(str(manifest_path))

        self.assertEqual(list(images.keys()), ["image_001"])
        self.assertEqual(images["image_001"]["path"], str(image_path))

    def test_build_agent_image_requests_uses_stable_ids_and_workspace_paths(self):
        tmp_path = SCRIPTS / self._testMethodName
        tmp_path.mkdir(exist_ok=True)
        self.addCleanup(lambda: self._remove_tree(tmp_path))
        article_path = tmp_path / "article.html"
        article_html = (
            "<html><body>"
            "<p>这段介绍 AI Agent 入门的任务拆解、工具调用和记忆管理。</p>"
            "<p>另一段介绍 Claude Code 的终端协作。</p>"
            "</body></html>"
        )
        article_path.write_text(article_html, encoding="utf-8")
        items = [{"title": "AI Agent 入门"}, {"name": "Claude Code"}]
        rules = {"agent_generate": {"width": 670, "height": 380}}

        requests = illustration_gen.build_agent_image_requests(
            article_path=str(article_path),
            article_type="深度解析",
            items=items,
            rules=rules,
            image_strategy="auto",
            max_count=2,
            article_html=article_html,
        )

        self.assertEqual([req["id"] for req in requests], ["image_001", "image_002"])
        self.assertEqual(requests[0]["width"], 670)
        self.assertEqual(requests[0]["height"], 380)
        self.assertEqual(
            Path(requests[0]["output_path"]),
            article_path.parent / "article-image-01.png",
        )
        self.assertIn("AI Agent 入门", requests[0]["prompt"])
        self.assertIn("paragraph_context", requests[0])
        self.assertIn("任务拆解、工具调用和记忆管理", requests[0]["paragraph_context"])
        self.assertIn("根据所在段落的具体信息", requests[0]["prompt"])

    def test_article_image_output_path_is_flat_next_to_article(self):
        article_path = Path("/Users/mulin/workspace/公众号/文章/2026年06月/0605-demo.html")

        image_path = illustration_gen.article_image_output_path(article_path, 1)

        self.assertEqual(
            image_path,
            Path("/Users/mulin/workspace/公众号/文章/2026年06月/0605-demo-image-01.png"),
        )

    def test_build_agent_image_requests_prefers_section_context(self):
        items = [
            {
                "title": "为什么端侧模型会变快",
                "html": "<p>这一节解释端侧模型通过缓存、量化和小模型协同降低延迟。</p>",
            }
        ]

        requests = illustration_gen.build_agent_image_requests(
            article_path="article.html",
            article_type="深度解析",
            items=items,
            rules={"agent_generate": {}},
            image_strategy="agent_first",
            max_count=1,
            article_html="<p>无关段落</p>",
        )

        self.assertEqual(requests[0]["context_source"], "section_html")
        self.assertIn("缓存、量化和小模型协同", requests[0]["paragraph_context"])

    @staticmethod
    def _remove_tree(path: Path):
        if not path.exists():
            return
        for child in path.iterdir():
            child.unlink()
        path.rmdir()


if __name__ == "__main__":
    unittest.main()
