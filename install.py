#!/usr/bin/env python3
"""Install the nested skill from a GitHub or local ZIP using only Python's stdlib.

The destination is a skills parent directory. Existing skills are never replaced.
No archive code is executed and no dependencies are installed by this program.
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

DEFAULT_REPO = "CEvildreaming/-schematic-deep-review"
DEFAULT_REF = "main"
SKILL_NAME = "schematic-deep-review"
SKILL_PATH = "skills/" + SKILL_NAME
MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024
MAX_UNPACKED_BYTES = 128 * 1024 * 1024
MAX_MEMBERS = 4000
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)
}


class InstallError(Exception):
    """An actionable installation failure, safe to show without a traceback."""


def default_destination() -> Path:
    """Current Codex user-skill discovery location; legacy installs use --dest."""
    return Path.home() / ".agents" / "skills"


def github_zip_url(repo: str, ref: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9_.-]+", repo) or repo.rsplit("/", 1)[-1] in {".", ".."}:
        raise InstallError("--repo must be an owner/repository pair.")
    if not ref or any(ord(c) < 32 for c in ref):
        raise InstallError("--ref must be a nonempty branch, tag or commit.")
    return f"https://codeload.github.com/{repo}/zip/{urllib.parse.quote(ref, safe='')}"


def download_archive(url: str, output: Path, timeout: float) -> None:
    if not math.isfinite(timeout) or timeout <= 0:
        raise InstallError("--timeout must be a positive, finite number of seconds.")
    request = urllib.request.Request(url, headers={"User-Agent": "schematic-deep-review-installer/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, output.open("xb") as stream:
            total = 0
            while chunk := response.read(64 * 1024):
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise InstallError("Archive download exceeds the 32 MiB limit.")
                stream.write(chunk)
    except urllib.error.HTTPError as exc:
        raise InstallError(f"GitHub download failed (HTTP {exc.code}); check --repo and --ref, or use --zip.") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise InstallError(f"Archive download failed: {exc}. Retry or use --zip for an offline archive.") from exc


def archive_members(archive: zipfile.ZipFile) -> list[tuple[zipfile.ZipInfo, PurePosixPath]]:
    """Validate every entry before extracting anything, on every host platform."""
    infos = archive.infolist()
    if not infos or len(infos) > MAX_MEMBERS:
        raise InstallError("Archive is empty or contains too many entries.")
    if sum(i.file_size for i in infos) > MAX_UNPACKED_BYTES:
        raise InstallError("Archive exceeds the 128 MiB unpacked-size limit.")
    result = []
    seen = {}
    for info in infos:
        name = info.orig_filename
        if "\x00" in name or "\\" in name or name.startswith("/"):
            raise InstallError(f"Unsafe ZIP path: {name!r}")
        raw = name.rstrip("/").split("/")
        if not raw or any(not part or part in {".", ".."} or ":" in part
                          or part.endswith((" ", ".")) or any(ord(c) < 32 for c in part)
                          or part.split(".")[0].upper() in _RESERVED for part in raw):
            raise InstallError(f"Unsafe ZIP path: {name!r}")
        mode = (info.external_attr >> 16) & 0xFFFF
        kind = stat.S_IFMT(mode)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or info.flag_bits & 1:
            raise InstallError(f"Links, special files and encrypted entries are not supported: {name!r}")
        path = PurePosixPath(*raw)
        key = str(path).casefold()
        if key in seen:
            raise InstallError(f"Duplicate or case-colliding ZIP path: {name!r}")
        seen[key] = info.is_dir()
        result.append((info, path))
    for _, path in result:
        if any(str(parent).casefold() in seen and not seen[str(parent).casefold()]
               for parent in path.parents if str(parent) != "."):
            raise InstallError(f"ZIP file/directory conflict: {path}")
    return result


def extract_skill(archive_path: Path, staging: Path) -> Path:
    """Accept either a GitHub top-level folder or a ZIP of the repository contents."""
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = archive_members(archive)
            roots = []
            expected = ("skills", SKILL_NAME, "SKILL.md")
            for info, path in members:
                if not info.is_dir() and (path.parts == expected or
                   (len(path.parts) == 4 and path.parts[1:] == expected)):
                    roots.append(path.parent)
            if len(roots) != 1:
                raise InstallError(f"Expected exactly one nested {SKILL_PATH}/SKILL.md in the ZIP.")
            source_root = roots[0]
            skill = staging / SKILL_NAME
            skill.mkdir()
            total = 0
            for info, path in members:
                if not path.is_relative_to(source_root):
                    continue
                relative = path.relative_to(source_root)
                if str(relative) == ".":
                    continue
                target = skill.joinpath(*relative.parts)
                if not target.resolve().is_relative_to(skill.resolve()):
                    raise InstallError(f"ZIP path escapes the skill: {path}")
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("xb") as out:
                    while chunk := source.read(64 * 1024):
                        total += len(chunk)
                        if total > MAX_UNPACKED_BYTES:
                            raise InstallError("Extracted data exceeds the unpacked-size limit.")
                        out.write(chunk)
            if not (skill / "SKILL.md").read_text(encoding="utf-8").strip():
                raise InstallError("The nested SKILL.md is empty.")
            return skill
    except (zipfile.BadZipFile, UnicodeError, RuntimeError, EOFError) as exc:
        raise InstallError(f"Archive is not a usable skill ZIP: {exc}") from exc


def install(*, archive: Path | None = None, dest: Path | None = None,
            repo: str = DEFAULT_REPO, ref: str = DEFAULT_REF, timeout: float = 30) -> Path:
    destination = (dest if dest is not None else default_destination()).expanduser().resolve()
    target = destination / SKILL_NAME
    if os.path.lexists(target):
        raise InstallError(f"Destination already exists; nothing was changed: {target}")
    with tempfile.TemporaryDirectory(prefix="schematic-skill-install-") as scratch:
        staging = Path(scratch)
        if archive is None:
            archive = staging / "download.zip"
            download_archive(github_zip_url(repo, ref), archive, timeout)
        else:
            archive = Path(archive).expanduser().resolve()
            if not archive.is_file():
                raise InstallError(f"Local ZIP not found: {archive}")
        source = extract_skill(archive, staging)
        destination.mkdir(parents=True, exist_ok=True)
        try:
            target.mkdir()  # Exclusive reservation: never merge with an existing skill.
        except FileExistsError as exc:
            raise InstallError(f"Destination already exists; nothing was changed: {target}") from exc
        try:
            shutil.copytree(source, target, dirs_exist_ok=True)
        except Exception:
            shutil.rmtree(target)  # Only the destination exclusively created above.
            raise
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, dest="archive", help="Install an existing local repository ZIP (offline).")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub owner/repository for archive download.")
    parser.add_argument("--ref", default=DEFAULT_REF, help="GitHub branch, tag or commit; default: main.")
    parser.add_argument("--dest", type=Path, help="Skills parent directory; default: ~/.agents/skills. Legacy Codex: ~/.codex/skills.")
    parser.add_argument("--timeout", type=float, default=30, help="Network socket timeout in seconds; default: 30.")
    args = parser.parse_args(argv)
    try:
        target = install(**vars(args))
    except (InstallError, OSError, ValueError) as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Installed {SKILL_NAME} at {target}")
    print("No code was executed and no Python dependencies were installed. See the skill README for setup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
