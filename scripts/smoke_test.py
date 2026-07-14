from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epitaxy.pipeline import run_si, run_sic


def main():
    synthetic_file = ROOT / "data" / "synthetic" / "synthetic_附件1.xlsx"
    if not synthetic_file.exists():
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "generate_synthetic.py")])
    sic = run_sic(ROOT / "configs" / "synthetic_sic.yaml")
    si = run_si(ROOT / "configs" / "synthetic_si.yaml")
    result = {
        "sic_true_um": 12.5,
        "sic_two_beam_um": sic["joint_two_beam"]["thickness_um"],
        "si_true_um": 18.0,
        "si_tmm_um": si["joint_tmm"]["thickness_um"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if abs(result["sic_two_beam_um"] - 12.5) > 0.8:
        raise SystemExit("SiC synthetic smoke test failed")
    if abs(result["si_tmm_um"] - 18.0) > 1.5:
        raise SystemExit("Si synthetic smoke test failed")


if __name__ == "__main__":
    main()
