from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epitaxy.pipeline import run_sic


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "q2_sic.yaml"))
    args = parser.parse_args()
    print(json.dumps(run_sic(args.config), ensure_ascii=False, indent=2))
