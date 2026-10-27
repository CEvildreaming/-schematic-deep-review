"""Check local documentation links and accidental private material before release.

This is a bounded publication check, not a general-purpose secret scanner.
Run from any directory with: python tools/check_release.py
"""
from pathlib import Path
import json
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".venv", ".pytest_cache", ".local-validation", "output"}
SKIP_FILES = {"test-results.txt", ".DS_Store", "Thumbs.db"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".toml"}
TEXT_NAMES = {"LICENSE", ".gitignore", ".gitattributes"}
PUBLIC_IMAGES = {"examples/synthetic-rc/preview.png"}
PRIVATE_PATTERNS = {
    "personal Windows path": re.compile(r"(?i)[A-Z]:[\\/](?:Users|Desktop|Documents)[\\/]"),
    "private chat attachment": re.compile("(?:" + "wx" + "id_|xwechat" + "_files)", re.I),
    "credential-shaped value": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9]{32,})"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def release_files():
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts) or path.name in SKIP_FILES:
            continue
        if path.is_file() or path.is_symlink():
            yield path


def main():
    errors = []
    count = 0
    links = 0
    for path in release_files():
        rel = path.relative_to(ROOT).as_posix()
        count += 1
        if path.is_symlink():
            errors.append(f"{rel}: symlink requires explicit review")
            continue
        if rel in PUBLIC_IMAGES:
            continue
        if path.name not in TEXT_NAMES and path.suffix not in TEXT_SUFFIXES:
            errors.append(f"{rel}: unexpected release file type")
            continue
        text = path.read_text(encoding="utf-8-sig")
        for label, pattern in PRIVATE_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{rel}: {label}")
        if path.suffix == ".md":
            for match in re.finditer(r"!?\[[^\]\n]+\]\(([^)]+)\)", text):
                target = match.group(1).strip().split(' "')[0].strip("<>")
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                target = unquote(target.split("#", 1)[0])
                if not target:
                    continue
                linked = (path.parent / target).resolve()
                if not linked.is_relative_to(ROOT) or not linked.exists():
                    errors.append(f"{rel}: missing/outside local link: {target}")
                links += 1
    print(json.dumps({"passed": not errors, "files_checked": count, "local_links_checked": links, "errors": errors}, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
