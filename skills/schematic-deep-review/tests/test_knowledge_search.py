"""Literal retrieval tests with local Markdown fixtures and a stdlib-only CLI."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/knowledge_search.py"
spec = importlib.util.spec_from_file_location("knowledge_search", SCRIPT)
knowledge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(knowledge)


class TestKnowledgeSearch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="knowledge-search-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "power.md").write_text("# 电源\n通用说明。\n## LDO 温升\n功耗=(输入电压-输出电压)×电流。\n温升取决于热阻。\n## RC 电路\n10 kΩ × 0.1 μF = 1 ms。\n", encoding="utf-8")
        (self.root / "other.md").write_text("# 其它\nRC 数据，未说明温升。\n", encoding="utf-8")

    def test_chinese_keywords_return_heading_path_and_exact_lines(self):
        result = knowledge.search(self.root, "LDO 温升")
        self.assertEqual(len(result), 1)
        self.assertEqual((result[0]["path"], result[0]["heading"], result[0]["start_line"]), ("power.md", "LDO 温升", 3))
        self.assertIn("5: 温升取决于热阻。", result[0]["excerpt"])

    def test_all_terms_must_match_one_section_and_no_results_are_empty(self):
        self.assertEqual(knowledge.search(self.root, "LDO RC"), [])
        self.assertEqual(knowledge.search(self.root, "不存在"), [])

    def test_unicode_normalization_case_insensitive_ranking_and_limit(self):
        result = knowledge.search(self.root, "ｒｃ", limit=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["heading"], "RC 电路")
        self.assertEqual(knowledge.search(self.root, "Ω")[0]["path"], "power.md")

    def test_code_fence_headings_do_not_split_sections(self):
        (self.root / "code.md").write_text("# Example\n```python\n# not-a-section\nvalue = 'needle'\n```\n", encoding="utf-8")
        result = knowledge.search(self.root, "needle")
        self.assertEqual(result[0]["heading"], "Example")
        self.assertIn("4: value", result[0]["excerpt"])

    def test_invalid_queries_paths_and_limits_fail_clearly(self):
        for query, limit in [("  ", 5), ("LDO", 0), ("LDO", 101)]:
            with self.assertRaises(ValueError):
                knowledge.search(self.root, query, limit)
        with self.assertRaisesRegex(ValueError, "directory not found"):
            knowledge.search(self.root / "missing", "RC")

    def test_real_stdlib_only_json_cli(self):
        command = [sys.executable, "-S", "-X", "utf8", str(SCRIPT), "LDO 温升", "--root", str(self.root), "--json"]
        run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 0, run.stderr)
        data = json.loads(run.stdout)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["path"], "power.md")


if __name__ == "__main__":
    unittest.main()
