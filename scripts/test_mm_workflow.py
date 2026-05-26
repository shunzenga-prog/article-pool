import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import validate_mm_workflow


class MultimodalWorkflowTests(unittest.TestCase):
    def test_mm_article_assets_are_installable_and_isolated(self):
        report = validate_mm_workflow.validate_project(ROOT)

        self.assertEqual(report["skill"]["name"], "mm-article")
        self.assertEqual(report["manifest"]["skill"], "mm-article")
        self.assertEqual(report["plugin"]["skills"], "./skills/")
        self.assertEqual(report["legacy_lane"]["mode"], "preserved")
        self.assertIn("article-pipeline", report["legacy_lane"]["protected_skills"])
        self.assertIn("scripts/publish_html.py", report["legacy_lane"]["protected_tools"])

    def test_semantic_tasks_do_not_reduce_to_script_adapters(self):
        report = validate_mm_workflow.validate_project(ROOT)

        task_kinds = {task["kind"] for task in report["manifest"]["semantic_tasks"]}
        required = {
            "research.topic",
            "draft.article",
            "plan.visuals",
            "generate.image",
            "inspect.visual",
            "review.wechat_render",
            "publish.draft",
        }

        self.assertTrue(required.issubset(task_kinds))
        self.assertGreaterEqual(report["manifest"]["semantic_task_count"], 7)

    def test_mm_article_covers_core_authoring_controls(self):
        report = validate_mm_workflow.validate_project(ROOT)
        skill_text = (ROOT / "skills" / "mm-article" / "SKILL.md").read_text(encoding="utf-8")

        task_kinds = {task["kind"] for task in report["manifest"]["semantic_tasks"]}
        required_tasks = {
            "title.generate",
            "draft.prompt",
            "research.timeliness",
            "research.sources",
            "layout.wechat",
            "validate.format",
            "rewrite.humanize",
            "review.editorial",
        }
        required_sections = [
            "标题生成约束",
            "文章内容提示词",
            "时效性校验",
            "搜索来源",
            "排版",
            "格式校验",
            "去 AI 味",
            "审阅",
        ]

        self.assertTrue(required_tasks.issubset(task_kinds))
        for section in required_sections:
            self.assertIn(section, skill_text)

    def test_mm_article_has_production_grade_standards(self):
        report = validate_mm_workflow.validate_project(ROOT)
        skill_text = (ROOT / "skills" / "mm-article" / "SKILL.md").read_text(encoding="utf-8")
        standards_path = ROOT / "skills" / "mm-article" / "references" / "production-standards.md"
        standards_text = standards_path.read_text(encoding="utf-8")

        required_ids = {
            "platform_contract",
            "topic_dedup",
            "source_reliability",
            "timeliness",
            "evidence_ledger",
            "claim_boundary",
            "title_quality",
            "content_prompt",
            "narrative_structure",
            "human_voice",
            "reader_visible_process_leak",
            "wechat_layout",
            "format_validation",
            "visual_truthfulness",
            "multimodal_assets",
            "accessibility",
            "compliance_safety",
            "privacy_secrets",
            "editorial_review",
            "publish_readiness",
            "failure_handling",
            "observability",
            "legacy_isolation",
        }
        standards = report["manifest"]["production_standards"]
        standard_ids = {item["id"] for item in standards}

        self.assertIn("references/production-standards.md", skill_text)
        self.assertTrue(required_ids.issubset(standard_ids))
        self.assertGreaterEqual(report["manifest"]["production_standard_count"], 22)
        for item in standards:
            self.assertTrue(item.get("gate"))
            self.assertTrue(item.get("failure_mode"))

        for heading in [
            "生产级总则",
            "P0 阻断门禁",
            "证据与时效",
            "内容与标题",
            "排版与格式",
            "多模态资产",
            "安全与合规",
            "审阅与发布",
            "失败处理与可观测性",
        ]:
            self.assertIn(heading, standards_text)

    def test_reader_visible_process_leak_detector_flags_creator_notes(self):
        bad_html = (
            '<p><span>图：官方仓库截图裁切版。'
            "事实型界面图优先用官方截图，不用生成图替代。</span></p>"
        )
        good_html = '<p><span>图：cc-connect 官方仓库中的飞书对话示例。</span></p>'

        leaks = validate_mm_workflow.detect_reader_visible_process_leaks(bad_html)

        self.assertGreaterEqual(len(leaks), 2)
        self.assertEqual(validate_mm_workflow.detect_reader_visible_process_leaks(good_html), [])

    def test_semantic_task_dataflow_is_closed(self):
        report = validate_mm_workflow.validate_project(ROOT)

        self.assertEqual(report["manifest"]["dataflow_errors"], [])

    def test_output_illustration_and_cover_contracts_are_explicit(self):
        report = validate_mm_workflow.validate_project(ROOT)
        manifest = report["manifest"]
        skill_text = (ROOT / "skills" / "mm-article" / "SKILL.md").read_text(encoding="utf-8")
        output_spec = (ROOT / "skills" / "mm-article" / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )

        output = manifest["output_contract"]
        wechat = output["wechat"]
        reports = output["reports"]
        illustration = manifest["illustration_policy"]
        cover = manifest["cover_policy"]

        self.assertEqual(output["base_dir"], "文章/{YYYY}年{MM}月")
        self.assertEqual(output["basename"], "{MMDD}-{safe_title}")
        self.assertEqual(wechat["draft_html"], "文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.html")
        self.assertEqual(wechat["illustrated_html"], "文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_illustrated.html")
        self.assertEqual(wechat["cdn_html"], "文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_cdn.html")
        self.assertEqual(wechat["cover_png"], "文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.png")
        self.assertEqual(wechat["visual_dir"], "文章/{YYYY}年{MM}月/{visual_slug}")
        self.assertIn("images_claude_agent_view", wechat["visual_slug_examples"])
        self.assertIn("screenshots_ep5", wechat["visual_slug_examples"])
        self.assertIn("image_requests.json", reports["image_requests"])
        self.assertIn("generated_images.json", reports["generated_images"])
        self.assertEqual(illustration["default_strategy"], "agent_first_when_available")
        self.assertEqual(illustration["agent_first_flow"][0], "emit_image_requests")
        self.assertEqual(cover["final_cover"], wechat["cover_png"])
        self.assertEqual(cover["agent_background"], wechat["cover_background"])

        self.assertIn("references/output-contract.md", skill_text)
        for heading in ["旧文章格式基线", "输出目录", "正文 HTML 格式", "配图流程", "封面图生成", "发布前输出检查"]:
            self.assertIn(heading, output_spec)

    def test_cover_generation_requires_article_specific_brief_and_truthful_model_claims(self):
        skill_text = (ROOT / "skills" / "mm-article" / "SKILL.md").read_text(encoding="utf-8")
        standards_text = (
            ROOT / "skills" / "mm-article" / "references" / "production-standards.md"
        ).read_text(encoding="utf-8")
        output_spec = (ROOT / "skills" / "mm-article" / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )

        required_skill_phrases = [
            "cover_brief_artifact",
            "从文章内容提炼",
            "品牌视觉元素",
            "不得声称底层模型名",
            "普通素材站科技图",
            "用户反馈封面",
        ]
        for phrase in required_skill_phrases:
            self.assertIn(phrase, skill_text)

        for phrase in [
            "封面泛化",
            "内置生图工具未暴露模型名",
            "重新生成封面",
        ]:
            self.assertIn(phrase, standards_text)

        for phrase in [
            "文章主张",
            "品牌元素",
            "审美失败",
        ]:
            self.assertIn(phrase, output_spec)


if __name__ == "__main__":
    unittest.main()
