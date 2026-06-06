import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import review_html


class ReviewHtmlTests(unittest.TestCase):
    def test_formulaic_ai_phrases_are_hard_failures(self):
        html = """
<p style="margin:10px 0 0 0;text-align:left;"><span style="font-size:15px;color:#2c2c2c;line-height:1.85;">先说结论，这件事不是普通升级。</span></p>
<p style="margin:10px 0 0 0;text-align:left;"><span style="font-size:15px;color:#2c2c2c;line-height:1.85;">尽管它看起来很强，但是真正的变化还在后面。</span></p>
<p style="margin:10px 0 0 0;text-align:left;"><span style="font-size:15px;color:#2c2c2c;line-height:1.85;">总结一下，用户现在多了一个选择。</span></p>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "0606-test.html"
            path.write_text(html, encoding="utf-8")

            result = review_html.review(str(path))

        self.assertFalse(result["passed"])
        self.assertEqual(result["hard_checks"]["h5_ai_formulaic_phrases"]["status"], "FAIL")
        self.assertGreaterEqual(result["hard_checks"]["h5_ai_formulaic_phrases"]["count"], 3)
        self.assertTrue(any("AI 套话" in failure for failure in result["failures"]))


if __name__ == "__main__":
    unittest.main()
