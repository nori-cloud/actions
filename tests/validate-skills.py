"""Check the distributable OpenCode catalog without external dependencies."""

import json
import re
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "skills"


class SkillCatalogTests(unittest.TestCase):
    def test_catalog_entries(self):
        entries = json.loads((CATALOG / "index.json").read_text())["skills"]
        self.assertTrue(entries)
        names = [entry["name"] for entry in entries]
        self.assertEqual(len(names), len(set(names)))
        for entry in entries:
            with self.subTest(skill=entry["name"]):
                name = entry["name"]
                self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
                self.assertLessEqual(len(name), 64)
                self.assertIsInstance(entry["version"], str)
                self.assertTrue(entry["version"])
                files = entry["files"]
                self.assertTrue(files)
                self.assertEqual(len(files), len(set(files)))
                self.assertIn("SKILL.md", files)
                for filename in files:
                    relative = PurePosixPath(filename)
                    self.assertFalse(relative.is_absolute())
                    self.assertNotIn("..", relative.parts)
                    self.assertNotIn("\\", filename)
                    self.assertNotIn(":", filename)
                    path = CATALOG / name / filename
                    self.assertTrue(path.resolve().is_relative_to(CATALOG.resolve()))
                    self.assertTrue(path.is_file(), str(path))
                text = (CATALOG / name / "SKILL.md").read_text()
                frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
                self.assertIsNotNone(frontmatter)
                metadata = frontmatter[1]
                self.assertRegex(metadata, rf"(?m)^name: {re.escape(name)}$")
                self.assertRegex(metadata, r"(?m)^description: \S.+$")

    def test_install_example(self):
        readme = (ROOT / "README.md").read_text()
        example = re.search(r"```json\n(.*?)\n```", readme, re.S)
        self.assertIsNotNone(example)
        config = json.loads(example[1])
        self.assertEqual(config["$schema"], "https://opencode.ai/config.json")
        self.assertIn(
            "https://raw.githubusercontent.com/nori-cloud/actions/main/skills/",
            config["skills"],
        )


if __name__ == "__main__":
    unittest.main()
