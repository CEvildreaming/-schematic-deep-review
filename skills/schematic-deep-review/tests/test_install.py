"""Offline installer tests; no GitHub calls or user-skill writes."""
import importlib.util
import io
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error
import warnings
import zipfile

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("skill_install", REPO / "install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class TestInstaller(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skill-installer-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dest = self.root / "user-skills"
        self.zip = self.root / "repo.zip"

    def archive(self, extras=None, prefix="repo-main/"):
        with zipfile.ZipFile(self.zip, "w") as archive:
            archive.writestr(prefix + "README.md", "Repository content is not installed.")
            archive.writestr(prefix + installer.SKILL_PATH + "/SKILL.md", "---\nname: schematic-deep-review\n---\nTest only.")
            archive.writestr(prefix + installer.SKILL_PATH + "/knowledge/test.md", "# 中文\nRC 电路\n")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                for name, content in extras or []:
                    archive.writestr(name, content)
        return self.zip

    def test_local_zip_installs_only_nested_skill(self):
        result = installer.install(archive=self.archive(), dest=self.dest)
        self.assertEqual(result, (self.dest / installer.SKILL_NAME).resolve())
        self.assertIn("RC 电路", (result / "knowledge/test.md").read_text(encoding="utf-8"))
        self.assertFalse((result / "README.md").exists())
        self.assertEqual([p.resolve() for p in self.dest.iterdir()], [result])

    def test_repository_contents_zip_without_wrapper_folder(self):
        result = installer.install(archive=self.archive(prefix=""), dest=self.dest)
        self.assertTrue((result / "SKILL.md").is_file())

    def test_default_destination_is_current_agents_location(self):
        self.assertEqual(installer.DEFAULT_REPO, "CEvildreaming/-schematic-deep-review")
        self.assertEqual(installer.github_zip_url(installer.DEFAULT_REPO, "main"),
                         "https://codeload.github.com/CEvildreaming/-schematic-deep-review/zip/main")
        with mock.patch.object(Path, "home", return_value=self.root):
            self.assertEqual(installer.default_destination(), self.root / ".agents/skills")

    def test_existing_skill_is_not_touched_or_downloaded(self):
        target = self.dest / installer.SKILL_NAME
        target.mkdir(parents=True)
        marker = target / "keep.txt"
        marker.write_bytes(b"user content")
        with mock.patch.object(installer, "download_archive") as download:
            with self.assertRaisesRegex(installer.InstallError, "already exists"):
                installer.install(dest=self.dest)
            download.assert_not_called()
        self.assertEqual(marker.read_bytes(), b"user content")
        self.assertEqual(list(target.iterdir()), [marker])

    def test_existing_empty_directory_is_not_replaced(self):
        target = self.dest / installer.SKILL_NAME
        target.mkdir(parents=True)
        with self.assertRaisesRegex(installer.InstallError, "already exists"):
            installer.install(archive=self.archive(), dest=self.dest)
        self.assertEqual(list(target.iterdir()), [])

    def test_path_traversal_and_windows_paths_rejected_before_install(self):
        for name in ["../escape.txt", "/absolute.txt", "repo/../../escape.txt",
                     "C:/escape.txt", "repo\\..\\escape.txt", "repo/NUL.txt", "repo/name. /bad"]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(installer.InstallError, "Unsafe ZIP path"):
                    installer.install(archive=self.archive([(name, "bad")]), dest=self.dest)
                self.assertFalse(self.dest.exists())
                self.assertFalse((self.root / "escape.txt").exists())

    def test_symlink_member_rejected(self):
        info = zipfile.ZipInfo("repo-main/skills/schematic-deep-review/link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaisesRegex(installer.InstallError, "Links"):
            installer.install(archive=self.archive([(info, "../../outside")]), dest=self.dest)
        self.assertFalse(self.dest.exists())

    def test_duplicate_case_and_file_directory_conflict_rejected(self):
        for extras in [[("repo-main/README.md", "duplicate")],
                       [("repo-main/readme.MD", "case duplicate")],
                       [("repo-main/README.md/subfile", "conflict")]]:
            with self.subTest(extras=extras):
                with self.assertRaises(installer.InstallError):
                    installer.install(archive=self.archive(extras), dest=self.dest)
                self.assertFalse(self.dest.exists())

    def test_ambiguous_skill_and_invalid_zip_rejected(self):
        duplicate = "second/skills/schematic-deep-review/SKILL.md"
        with self.assertRaisesRegex(installer.InstallError, "exactly one"):
            installer.install(archive=self.archive([(duplicate, "extra")]), dest=self.dest)
        self.zip.write_bytes(b"<html>not a zip</html>")
        with self.assertRaises(installer.InstallError):
            installer.install(archive=self.zip, dest=self.dest)
        self.assertFalse(self.dest.exists())

    def test_unpacked_size_limit(self):
        with mock.patch.object(installer, "MAX_UNPACKED_BYTES", 20):
            with self.assertRaisesRegex(installer.InstallError, "unpacked-size"):
                installer.install(archive=self.archive(), dest=self.dest)
        self.assertFalse(self.dest.exists())

    def test_copy_failure_removes_only_new_partial_target(self):
        self.dest.mkdir()
        sentinel = self.dest / "another-skill.txt"
        sentinel.write_bytes(b"preserve")
        with mock.patch.object(installer.shutil, "copytree", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                installer.install(archive=self.archive(), dest=self.dest)
        self.assertFalse((self.dest / installer.SKILL_NAME).exists())
        self.assertEqual(sentinel.read_bytes(), b"preserve")

    def test_download_timeout_and_http_errors_are_actionable(self):
        for error in [TimeoutError("timed out"), urllib.error.HTTPError("https://example.invalid", 404, "missing", {}, None)]:
            with self.subTest(error=error):
                with mock.patch.object(installer.urllib.request, "urlopen", side_effect=error) as request:
                    with self.assertRaisesRegex(installer.InstallError, "download failed"):
                        installer.download_archive("https://example.invalid/archive.zip", self.root / "download.zip", 7)
                    self.assertEqual(request.call_args.kwargs["timeout"], 7)

    def test_download_size_limit_and_ref_url_encoding(self):
        self.assertEqual(installer.github_zip_url("owner/repo", "feature/test"), "https://codeload.github.com/owner/repo/zip/feature%2Ftest")
        with self.assertRaises(installer.InstallError):
            installer.github_zip_url("../unsafe", "main")
        with mock.patch.object(installer.urllib.request, "urlopen", return_value=io.BytesIO(b"12345")):
            with mock.patch.object(installer, "MAX_DOWNLOAD_BYTES", 4):
                with self.assertRaisesRegex(installer.InstallError, "download exceeds"):
                    installer.download_archive("https://example.invalid/x", self.root / "download.zip", 1)

    def test_actual_stdlib_only_cli_install_and_refusal(self):
        command = [sys.executable, "-S", "-X", "utf8", str(REPO / "install.py"),
                   "--zip", str(self.archive()), "--dest", str(self.dest)]
        first = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("Installed schematic-deep-review", first.stdout)
        second = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(second.returncode, 1)
        self.assertIn("already exists", second.stderr)


if __name__ == "__main__":
    unittest.main()
