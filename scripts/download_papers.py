#!/usr/bin/env python3
"""
Download papers listed in a JSON file (e.g., resources/included_papers_20250825_balanced.json).

The script looks for keys like `url_pdf` or `arxiv_id` to construct a PDF URL.
By default, it only downloads entries where `is_included` is true.

Usage examples:
  python scripts/download_papers.py \
    --json resources/included_papers_20250825_balanced.json \
    --out-dir datasets/papers \
    --concurrency 6

  # Download all entries (ignore is_included flag)
  python scripts/download_papers.py --json resources/included_papers_20250825_balanced.json --all

Dependencies: requests, tqdm (already in requirements.txt)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests
from tqdm import tqdm

# Reuse project helpers if available; fall back if not present
try:
    from src.modules.utils import sanitize_filename, save_result
except Exception:
    def sanitize_filename(filename: str) -> str:
        return re.sub(r'[\\/:"*?<>|]', "_", filename)

    def save_result(result: str, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(result, encoding="utf-8")


DEFAULT_JSON = Path("resources/included_papers_20250825_balanced.json")
DEFAULT_OUT_DIR = Path("datasets/papers")


@dataclass
class Paper:
    raw: Dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.raw.get("id") or self.raw.get("arxiv_id") or self.raw.get("title") or "paper")

    @property
    def title(self) -> str:
        return str(self.raw.get("title") or self.id)

    @property
    def url_pdf(self) -> Optional[str]:
        url = self.raw.get("url_pdf")
        if isinstance(url, str) and url.strip():
            return url.strip()
        # Fallback for arXiv
        arxiv_id = self.raw.get("arxiv_id")
        if isinstance(arxiv_id, str) and arxiv_id:
            return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        return None

    @property
    def is_included(self) -> bool:
        val = self.raw.get("is_included")
        # Default to True if flag missing; otherwise cast to bool
        return True if val is None else bool(val)

    def target_filename(self) -> str:
        id_part = sanitize_filename(self.id)[:64]
        title_part = sanitize_filename(self.title)[:120]
        base = f"{id_part} - {title_part}".strip().rstrip("- ")
        return base + ".pdf"


def load_papers(json_path: Path) -> list[Paper]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {json_path}, got: {type(data)}")
    return [Paper(item) for item in data]


def download_one(session: requests.Session, paper: Paper, out_dir: Path, overwrite: bool, timeout: int, chunk_size: int = 1 << 14) -> Tuple[str, bool, str]:
    url = paper.url_pdf
    if not url:
        return paper.id, False, "no url_pdf or arxiv_id"

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / paper.target_filename()

    if out_path.exists() and not overwrite:
        return str(out_path), True, "exists"

    try:
        with session.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            # Optional: basic content-type sanity check
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "pdf" not in ctype and not ctype:
                # Some servers may omit; proceed but note
                pass

            with out_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
        return str(out_path), True, "ok"
    except requests.RequestException as e:
        return url, False, f"request_error: {e}" 
    except Exception as e:
        return url, False, f"error: {e}"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Download papers from a JSON list.")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="Path to JSON file with paper entries")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory to save PDFs")
    parser.add_argument("--all", action="store_true", help="Download all entries (ignore is_included flag)")
    parser.add_argument("--max", type=int, default=0, help="Max number of papers to download (0 = no limit)")
    parser.add_argument("--concurrency", type=int, default=6, help="Number of concurrent downloads")
    parser.add_argument("--timeout", type=int, default=45, help="Per-request timeout in seconds")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be downloaded without fetching")
    args = parser.parse_args(argv)

    if not args.json.exists():
        print(f"JSON not found: {args.json}", file=sys.stderr)
        return 2

    papers = load_papers(args.json)
    if not args.all:
        papers = [p for p in papers if p.is_included]

    if args.max and args.max > 0:
        papers = papers[: args.max]

    if args.dry_run:
        for p in papers:
            print(f"DRY-RUN: {p.url_pdf or 'NO_URL'} -> {args.out_dir / p.target_filename()}")
        print(f"Total: {len(papers)} (dry-run)")
        return 0

    ok_count = 0
    fail_count = 0
    failures: list[Tuple[str, str]] = []

    session = requests.Session()
    # Slightly polite default headers
    session.headers.update({
        "User-Agent": "SurveyX-Downloader/1.0 (+https://github.com/IAAR-Shanghai/SurveyX)",
        "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
    })

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        futures = [
            ex.submit(download_one, session, p, args.out_dir, args.overwrite, args.timeout)
            for p in papers
        ]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="downloading"):
            out, ok, msg = fut.result()
            if ok:
                ok_count += 1
            else:
                fail_count += 1
                failures.append((out, msg))

    # Save a manifest for inspection
    manifest_path = args.out_dir / "download_manifest.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for p in papers:
        lines.append(json.dumps({
            "id": p.id,
            "title": p.title,
            "url_pdf": p.url_pdf,
            "target": str(args.out_dir / p.target_filename()),
        }, ensure_ascii=False))
    save_result("\n".join(lines), manifest_path)

    if failures:
        fail_log = args.out_dir / "download_failures.txt"
        save_result("\n".join([f"{u}\t{m}" for u, m in failures]), fail_log)

    print(f"Done. ok={ok_count}, fail={fail_count}, out_dir={args.out_dir}")
    if failures:
        print(f"See failures: {fail_log}")
    print(f"Manifest: {manifest_path}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

