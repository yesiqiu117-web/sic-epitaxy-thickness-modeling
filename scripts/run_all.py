from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epitaxy.io import save_dataframe
from epitaxy.pipeline import run_si, run_sic
from epitaxy.reporting import (
    combined_markdown_report,
    final_results_dataframe,
    save_json,
    save_text,
)


def _load_existing() -> dict:
    report_dir = ROOT / "outputs" / "reports"
    paths = {
        "sic": report_dir / "q2_sic_summary.json",
        "si": report_dir / "q3_si_summary.json",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "缺少已有结果文件，无法复用：" + ", ".join(missing)
            + "。请改用 --recompute 从原始附件重新运行。"
        )
    return {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in paths.items()
    }


def _write_combined_outputs(result: dict) -> None:
    output = ROOT / "outputs"
    save_dataframe(
        final_results_dataframe(result["sic"], result["si"]),
        output / "tables" / "final_results.csv",
    )
    save_text(
        combined_markdown_report(result["sic"], result["si"]),
        output / "reports" / "final_results.md",
    )
    save_json(result, output / "reports" / "all_results.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="汇总已有实验结果，或从附件 1—4 完整重算全部实验。"
    )
    parser.add_argument(
        "--recompute",
        action="store_true",
        help="从 data/raw 中的附件重新执行拟合、Bootstrap、敏感性与 TMM 扫描。",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="不在终端打印完整 JSON，仅打印输出文件位置。",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.recompute:
        result = {
            "sic": run_sic(ROOT / "configs" / "q2_sic.yaml"),
            "si": run_si(ROOT / "configs" / "q3_si.yaml"),
        }
    else:
        result = _load_existing()

    _write_combined_outputs(result)

    if args.quiet:
        print("结果已写入 outputs/reports/final_results.md、outputs/tables/final_results.csv 和 outputs/reports/all_results.json")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
