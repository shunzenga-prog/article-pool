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

        self.assertEqual(output["article_root"], "/Users/mulin/workspace/公众号/文章")
        self.assertEqual(output["base_dir"], "/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月")
        self.assertEqual(output["basename"], "{MMDD}-{safe_title}")
        self.assertEqual(wechat["draft_html"], "/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.html")
        self.assertEqual(wechat["illustrated_html"], "/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_illustrated.html")
        self.assertEqual(wechat["cdn_html"], "/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_cdn.html")
        self.assertEqual(wechat["cover_png"], "/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.png")
        self.assertEqual(wechat["visual_dir"], "/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月")
        self.assertEqual(wechat["body_image_pattern"], "/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}-image-{NN}.png")
        self.assertIn("0605-claude code最新实践指南-image-01.png", wechat["visual_slug_examples"])
        self.assertIn("image_requests.json", reports["image_requests"])
        self.assertIn("generated_images.json", reports["generated_images"])
        self.assertEqual(illustration["default_strategy"], "agent_first_when_available")
        self.assertEqual(illustration["agent_first_flow"][0], "emit_image_requests")
        self.assertIn("paragraph_context", illustration["request_context_fields"])
        self.assertEqual(cover["default_strategy"], "agent_direct_final_cover")
        self.assertEqual(cover["final_cover"], wechat["cover_png"])
        self.assertNotIn("cover_background", wechat)
        self.assertNotIn("agent_background", cover)

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
            "不调用 `gen_cover.py --background-image`",
        ]:
            self.assertIn(phrase, output_spec)

    def test_garden_inspired_controls_are_integrated(self):
        report = validate_mm_workflow.validate_project(ROOT)
        skill_text = (ROOT / "skills" / "mm-article" / "SKILL.md").read_text(encoding="utf-8")
        standards_text = (
            ROOT / "skills" / "mm-article" / "references" / "production-standards.md"
        ).read_text(encoding="utf-8")
        garden_patterns = (
            ROOT / "skills" / "mm-article" / "references" / "garden-creation-patterns.md"
        ).read_text(encoding="utf-8")
        video_skill = (ROOT / "skills" / "mm-video" / "SKILL.md").read_text(encoding="utf-8")

        task_kinds = {task["kind"] for task in report["manifest"]["semantic_tasks"]}
        required_tasks = {
            "research.local_kb",
            "visual.prompt_mode",
            "repurpose.web_video",
        }
        self.assertTrue(required_tasks.issubset(task_kinds))

        required_standards = {
            "local_kb_retrieval",
            "image_mode_awareness",
            "article_video_repurpose",
        }
        standard_ids = {item["id"] for item in report["manifest"]["production_standards"]}
        self.assertTrue(required_standards.issubset(standard_ids))

        for phrase in [
            "references/garden-creation-patterns.md",
            "article-research-kb",
            "Mode B",
            "Mode C",
            "不要假装出图成功",
        ]:
            self.assertIn(phrase, skill_text)

        for phrase in [
            "分层索引",
            "最多 5 轮",
            "模式感知",
            "script.md",
            "outline.md",
        ]:
            self.assertIn(phrase, garden_patterns)

        for phrase in [
            "web-video-presentation",
            "script.md",
            "outline.md",
            "16:9",
        ]:
            self.assertIn(phrase, video_skill)

        self.assertIn("image_mode_awareness", standards_text)

    def test_source_evidence_capture_runs_before_drafting_and_visual_planning(self):
        report = validate_mm_workflow.validate_project(ROOT)
        manifest = report["manifest"]
        skill_text = (ROOT / "skills" / "mm-article" / "SKILL.md").read_text(encoding="utf-8")
        output_spec = (ROOT / "skills" / "mm-article" / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )
        standards_text = (
            ROOT / "skills" / "mm-article" / "references" / "production-standards.md"
        ).read_text(encoding="utf-8")

        tasks = manifest["semantic_tasks"]
        task_kinds = [task["kind"] for task in tasks]
        task_by_kind = {task["kind"]: task for task in tasks}

        self.assertIn("evidence.source_capture", task_kinds)
        self.assertLess(task_kinds.index("research.topic"), task_kinds.index("evidence.source_capture"))
        self.assertLess(task_kinds.index("evidence.source_capture"), task_kinds.index("research.depth"))
        self.assertLess(task_kinds.index("evidence.source_capture"), task_kinds.index("draft.prompt"))
        self.assertLess(task_kinds.index("evidence.source_capture"), task_kinds.index("plan.visuals"))
        self.assertEqual(task_by_kind["evidence.source_capture"]["outputs"], ["source_capture_artifacts"])

        for downstream in ("research.depth", "draft.prompt", "draft.article", "plan.visuals", "capture.factual"):
            self.assertIn("source_capture_artifacts", task_by_kind[downstream]["inputs"])

        self.assertIn("source_capture", manifest["artifact_kinds"])
        self.assertIn("source_screenshot_pattern", manifest["output_contract"]["wechat"])
        self.assertIn("source_capture", manifest["output_contract"]["reports"])

        for phrase in ["原文证据截图", "source_capture_artifacts", "头像/账号/正文", "必要时间信息"]:
            self.assertIn(phrase, skill_text)
        for phrase in ["source-x-01-compact.png", "source_capture.json", "原文证据截图"]:
            self.assertIn(phrase, output_spec)
        for phrase in ["原文证据截图", "登录态", "侧栏", "私信"]:
            self.assertIn(phrase, standards_text)

    def test_visual_slot_coordination_prevents_duplicate_adjacent_images(self):
        report = validate_mm_workflow.validate_project(ROOT)
        manifest = report["manifest"]
        skill_text = (ROOT / "skills" / "mm-article" / "SKILL.md").read_text(encoding="utf-8")
        output_spec = (ROOT / "skills" / "mm-article" / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )
        standards_text = (
            ROOT / "skills" / "mm-article" / "references" / "production-standards.md"
        ).read_text(encoding="utf-8")

        illustration_policy = manifest["illustration_policy"]
        standard_ids = {item["id"] for item in manifest["production_standards"]}

        self.assertIn("slot_conflict_rules", illustration_policy)
        self.assertIn("visual_slot_conflict", standard_ids)

        joined_rules = "\n".join(illustration_policy["slot_conflict_rules"])
        for phrase in [
            "source_capture_artifacts",
            "same visual slot",
            "no consecutive visuals",
            "skip generated illustration",
        ]:
            self.assertIn(phrase, joined_rules)

        for phrase in ["同一位置", "连续插入多张图", "视觉槽位"]:
            self.assertIn(phrase, skill_text)
        for phrase in ["同一段落", "同一视觉槽位", "改为替换"]:
            self.assertIn(phrase, output_spec)
        for phrase in ["visual_slot_conflict", "连续图片", "相邻图片"]:
            self.assertIn(phrase, standards_text)

    def test_visual_provenance_gate_runs_before_scoring(self):
        report = validate_mm_workflow.validate_project(ROOT)
        manifest = report["manifest"]
        skill_text = (ROOT / "skills" / "mm-article" / "SKILL.md").read_text(encoding="utf-8")
        output_spec = (ROOT / "skills" / "mm-article" / "references" / "output-contract.md").read_text(
            encoding="utf-8"
        )
        standards_text = (
            ROOT / "skills" / "mm-article" / "references" / "production-standards.md"
        ).read_text(encoding="utf-8")

        gate = manifest["visual_provenance_gate"]
        standard_ids = {item["id"] for item in manifest["production_standards"]}

        self.assertEqual(
            gate["sequence"],
            ["classify_visual_need", "verify_source_provenance", "score_visual_quality"],
        )
        self.assertIn("visual_provenance_gate", standard_ids)
        self.assertIn("geometric", gate["reject_before_scoring"])
        self.assertIn("fallback_pattern", gate["reject_before_scoring"])
        self.assertIn("legacy_without_reason", gate["reject_before_scoring"])
        self.assertIn("source_capture_artifacts", gate["priority_sources"]["authority_social_post"])
        self.assertIn("agent_generated_local_image", gate["priority_sources"]["concept_illustration"])
        self.assertIn("agent_direct_final_cover", gate["priority_sources"]["concept_cover"])

        for phrase in ["先看图片来源", "再计算视觉得分", "authority_social_post"]:
            self.assertIn(phrase, skill_text)
        for phrase in ["verify_source_provenance", "legacy_without_reason", "geometric"]:
            self.assertIn(phrase, output_spec)
        for phrase in ["图片来源门禁", "评分前", "legacy_without_reason"]:
            self.assertIn(phrase, standards_text)


if __name__ == "__main__":
    unittest.main()
