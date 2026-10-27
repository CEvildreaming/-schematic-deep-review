#!/usr/bin/env python3
"""Search local Markdown knowledge by literal keywords, without third-party packages.

All query terms must occur in the same section, its heading, or its file name.
This is reproducible full-text retrieval, not semantic or electrical verification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata

DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "knowledge"
MAX_FILE_BYTES = 2 * 1024 * 1024


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def sections(text: str, fallback: str):
    lines = text.splitlines()
    title, start, fence = fallback, 0, None
    for index, line in enumerate(lines):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = value[0]
            elif value[0] == fence:
                fence = None
            continue
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line) if fence is None else None
        if heading:
            if any(part.strip() for part in lines[start:index]):
                yield title, start + 1, index, lines[start:index]
            title, start = heading.group(1), index
    if any(part.strip() for part in lines[start:]):
        yield title, start + 1, len(lines), lines[start:]


def search(root: Path, query: str, limit: int = 5) -> list[dict]:
    root = Path(root).expanduser().resolve()
    terms = list(dict.fromkeys(normalize(query).split()))
    if not terms:
        raise ValueError("Provide at least one nonempty keyword.")
    if not 1 <= limit <= 100:
        raise ValueError("--limit must be between 1 and 100.")
    if not root.is_dir():
        raise ValueError(f"Knowledge directory not found: {root}")
    results = []
    for path in sorted(root.rglob("*.md")):
        # Never follow linked files/directories outside (or inside) the knowledge tree.
        if not path.resolve().is_relative_to(root) or any(p.is_symlink() for p in [path, *path.parents] if p != root and p.is_relative_to(root)):
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"Knowledge file exceeds 2 MiB: {path.relative_to(root)}")
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8-sig")
        for heading, start, end, lines in sections(text, path.stem):
            body = normalize("\n".join(lines))
            location = normalize(relative + " " + heading)
            if not all(term in body or term in location for term in terms):
                continue
            selected = set()
            for i, line in enumerate(lines):
                if any(term in normalize(line) for term in terms):
                    selected.update(range(max(0, i - 1), min(len(lines), i + 2)))
            if not selected:
                selected.update(range(min(len(lines), 4)))
            indices = sorted(selected)[:14]
            excerpt = "\n".join(f"{start+i}: {lines[i]}" for i in indices)
            if len(excerpt) > 1600:
                excerpt = excerpt[:1600] + "…"
            score = sum(5 * location.count(term) + min(body.count(term), 10) for term in terms)
            results.append({"path": relative, "heading": heading, "start_line": start,
                            "end_line": end, "score": score, "matched_terms": terms,
                            "excerpt": excerpt})
    return sorted(results, key=lambda r: (-r["score"], r["path"], r["start_line"]))[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+", help="Literal keywords; separate terms with spaces.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Knowledge Markdown directory.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Print JSON suitable for an AI or another program.")
    args = parser.parse_args(argv)
    query = " ".join(args.query)
    try:
        results = search(args.root, query, args.limit)
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"Knowledge search failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"query": query, "count": len(results), "results": results}, ensure_ascii=False, indent=2))
    elif not results:
        print("No matching knowledge sections.")
    else:
        for item in results:
            print(f"{item['path']}:{item['start_line']}-{item['end_line']} | {item['heading']}")
            print(item["excerpt"])
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
