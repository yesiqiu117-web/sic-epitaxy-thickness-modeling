from __future__ import annotations

import argparse
import json

from .pipeline import run_si, run_sic


def main():
    parser = argparse.ArgumentParser(description="外延层厚度反演")
    sub = parser.add_subparsers(dest="command", required=True)
    p_sic = sub.add_parser("sic", help="运行问题 2 / SiC 分析")
    p_sic.add_argument("--config", default="configs/q2_sic.yaml")
    p_si = sub.add_parser("si", help="运行问题 3 / Si 分析")
    p_si.add_argument("--config", default="configs/q3_si.yaml")
    p_all = sub.add_parser("all", help="运行全部分析")
    p_all.add_argument("--sic-config", default="configs/q2_sic.yaml")
    p_all.add_argument("--si-config", default="configs/q3_si.yaml")
    args = parser.parse_args()
    if args.command == "sic":
        result = run_sic(args.config)
    elif args.command == "si":
        result = run_si(args.config)
    else:
        result = {"sic": run_sic(args.sic_config), "si": run_si(args.si_config)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
