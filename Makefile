.PHONY: install test synthetic smoke sic si all clean

install:
	python -m pip install -r requirements.txt
	python -m pip install -e .

test:
	pytest -q

synthetic:
	python scripts/generate_synthetic.py

smoke: synthetic
	python scripts/smoke_test.py

sic:
	python scripts/run_q2_sic.py --config configs/q2_sic.yaml

si:
	python scripts/run_q3_si.py --config configs/q3_si.yaml

all: sic si

clean:
	python -c "from pathlib import Path; import shutil; [shutil.rmtree(p, ignore_errors=True) for p in [Path('build'), Path('.pytest_cache')]]"
