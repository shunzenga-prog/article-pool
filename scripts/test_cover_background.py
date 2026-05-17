import sys
import unittest
from pathlib import Path

from PIL import Image


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import gen_cover


class CoverBackgroundTests(unittest.TestCase):
    def test_load_local_background_image_returns_rgb_image(self):
        tmp_dir = SCRIPTS / self._testMethodName
        tmp_dir.mkdir(exist_ok=True)
        self.addCleanup(lambda: self._remove_tree(tmp_dir))
        image_path = tmp_dir / "agent-cover.png"
        Image.new("RGB", (32, 18), "#336699").save(image_path)

        image, source = gen_cover.load_local_background_image(str(image_path))

        self.assertEqual(source, "agent-local")
        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.size, (32, 18))

    def test_load_local_background_image_ignores_missing_file(self):
        image, source = gen_cover.load_local_background_image("missing-cover.png")

        self.assertIsNone(image)
        self.assertIsNone(source)

    @staticmethod
    def _remove_tree(path: Path):
        if not path.exists():
            return
        for child in path.iterdir():
            child.unlink()
        path.rmdir()


if __name__ == "__main__":
    unittest.main()
