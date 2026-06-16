#!/usr/bin/env python3
"""
以 AI-Scientist-v2 的 LaTeX 工具函式為核心，對 sandbox/latex_assembly_demo 的 survey.tex
執行自動化修復（Unicode 清理、label 正規化、autoref 降級），並可選擇觸發
AI-Scientist 的 compile_latex 流程確認修復結果。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import unicodedata
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple


# --- 常數設定 -------------------------------------------------------------------
UNICODE_MAP = {
    "–": "--",
    "—": "---",
    "‑": "-",
    "−": "-",
    "→": r"$\rightarrow$",
    "←": r"$\leftarrow$",
    "↔": r"$\leftrightarrow$",
    "≈": r"$\approx$",
    "≤": r"$\leq$",
    "≥": r"$\geq$",
    "×": r"$\times$",
    "·": r"$\cdot$",
    "’": "'",
    "“": "``",
    "”": "''",
}

LABEL_PATTERN = re.compile(r"(\\label\{)([^}]+)\}")
REF_COMMANDS = ("\\ref", "\\autoref", "\\cref", "\\Cref")


def remove_accents_and_clean(text: str) -> str:
    """複製自 AI-Scientist `perform_writeup.py` 的清理函式。"""
    nfkd_form = unicodedata.normalize("NFKD", text)
    ascii_str = nfkd_form.encode("ASCII", "ignore").decode("ascii")
    ascii_str = re.sub(r"[^a-zA-Z0-9:_@\{\},-]+", "", ascii_str)
    return ascii_str.lower().strip()


@dataclass
class FixReport:
    target_file: str
    unicode_replacements: int = 0
    label_updates: int = 0
    autoref_updates: int = 0
    backup_path: str | None = None
    chktex_report: str | None = None
    compile_output: str | None = None


class LatexFixPipeline:
    """根據 latex_fix_module_plan.md 所述流程實作的簡易管線。"""

    def __init__(self, target_file: Path):
        self.target_file = target_file
        if not self.target_file.exists():
            raise FileNotFoundError(self.target_file)
        self.report = FixReport(target_file=str(self.target_file))

    # -- pipeline steps ---------------------------------------------------------
    def backup(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.target_file.with_suffix(
            f".backup_{timestamp}{self.target_file.suffix}"
        )
        shutil.copy2(self.target_file, backup_path)
        self.report.backup_path = str(backup_path)
        print(f"✓ 已備份原檔案 → {backup_path}")

    def load_text(self) -> str:
        return self.target_file.read_text(encoding="utf-8")

    def save_text(self, text: str) -> None:
        self.target_file.write_text(text, encoding="utf-8")
        print(f"✓ 已更新 {self.target_file}")

    def apply_unicode_fix(self, text: str) -> Tuple[str, int]:
        count = 0
        for bad, replacement in UNICODE_MAP.items():
            occurrences = text.count(bad)
            if occurrences:
                text = text.replace(bad, replacement)
                count += occurrences
        return text, count

    def normalize_labels(self, text: str) -> Tuple[str, Dict[str, str]]:
        replacements: Dict[str, str] = {}

        def _replace(match: re.Match[str]) -> str:
            original = match.group(2)
            cleaned = remove_accents_and_clean(original)
            cleaned = cleaned.strip("{}")
            if not cleaned:
                cleaned = f"label_{len(replacements)+1}"
            replacements[original] = cleaned
            return f"{match.group(1)}{cleaned}}}"

        new_text = LABEL_PATTERN.sub(_replace, text)
        return new_text, replacements

    def propagate_label_changes(self, text: str, replacements: Dict[str, str]) -> str:
        for old, new in replacements.items():
            if old == new:
                continue
            for cmd in REF_COMMANDS:
                text = text.replace(f"{cmd}{{{old}}}", f"{cmd}{{{new}}}")
        return text

    def normalize_autoref(self, text: str) -> Tuple[str, int]:
        pattern = re.compile(r"\\autoref\{([^}]+)\}")
        count = 0

        def _replace(match: re.Match[str]) -> str:
            nonlocal count
            label = match.group(1)
            prefix = "Figure"
            if label.startswith(("sec", "chapter", "subsec")):
                prefix = "Section"
            elif label.startswith(("tab", "table")):
                prefix = "Table"
            count += 1
            return f"{prefix}~\\ref{{{label}}}"

        new_text = pattern.sub(_replace, text)
        return new_text, count

    def run_demo_compile(self) -> str:
        demo_root = self.target_file.parent.parent
        cmd = ["bash", "scripts/compile_survey.sh"]
        print(f"RUNNING DEMO COMPILE: {' '.join(cmd)} (cwd={demo_root})")
        result = subprocess.run(
            cmd,
            cwd=demo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            check=False,
        )
        output = result.stdout.decode("utf-8", errors="ignore")
        pdf_path = demo_root / "survey.pdf"
        summary = f"demo compile {'succeeded' if pdf_path.exists() else 'failed'} (exit={result.returncode})"
        print(output)
        print(f"✓ {summary}")
        return summary

    def run_chktex(self) -> str:
        cmd = [
            "chktex",
            str(self.target_file),
            "-q",
            "-n2",
            "-n24",
            "-n13",
            "-n1",
        ]
        print(f"RUNNING CHKTEX: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        report = result.stdout
        report_path = self.target_file.parent / "latex_fix_chktex.txt"
        report_path.write_text(report, encoding="utf-8")
        self.report.chktex_report = str(report_path)
        print(f"✓ chktex finished (exit={result.returncode}); report → {report_path}")
        return report

    # -- orchestration ----------------------------------------------------------
    def run(self, run_compile: bool = False) -> FixReport:
        self.backup()
        text = self.load_text()

        text, unicode_count = self.apply_unicode_fix(text)
        self.report.unicode_replacements = unicode_count
        if unicode_count:
            print(f"✓ Unicode 取代 {unicode_count} 次")

        text, label_map = self.normalize_labels(text)
        self.report.label_updates = len(label_map)
        if label_map:
            print(f"✓ 正規化 label {len(label_map)} 個")
            text = self.propagate_label_changes(text, label_map)

        text, autoref_count = self.normalize_autoref(text)
        self.report.autoref_updates = autoref_count
        if autoref_count:
            print(f"✓ 轉換 autoref {autoref_count} 處")

        self.save_text(text)

        chktex_output = self.run_chktex()
        if chktex_output:
            print("=== chktex output (trimmed) ===")
            print("\n".join(chktex_output.splitlines()[:40]))

        if run_compile:
            self.report.compile_output = self.run_demo_compile()

        report_path = self.target_file.parent / "latex_fix_report.json"
        report_path.write_text(
            json.dumps(asdict(self.report), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"✓ 已輸出報告 → {report_path}")
        return self.report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI-Scientist LaTeX Fix Pipeline")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "compiled_output" / "survey.tex",
        help="要修復的 survey.tex 路徑",
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="完成修復後呼叫 AI-Scientist 的 compile_latex 進行驗證",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = LatexFixPipeline(args.target)
    report = pipeline.run(run_compile=args.compile)
    print("\n=== 修復摘要 ===")
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"❌ 修復流程失敗: {exc}")
        raise
    def run_chktex(self) -> str:
        cmd = [
            "chktex",
            str(self.target_file),
            "-q",
            "-n2",
            "-n24",
            "-n13",
            "-n1",
        ]
        print(f"RUNNING CHKTEX: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        report = result.stdout
        report_path = self.target_file.parent / "latex_fix_chktex.txt"
        report_path.write_text(report, encoding="utf-8")
        self.report.chktex_report = str(report_path)
        print(f"✓ chktex finished (exit={result.returncode}); report → {report_path}")
        return report
