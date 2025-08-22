# シンプル運用用Makefile（任意）

.PHONY: serve e2e pages-links check \
  fx-backtest-sample fx-export-sample fx-help \
  fx-optimize-sample fx-walkforward-sample fx-pipeline-quick \
  release-notes release-checklist

serve:
	@echo "Serving at http://localhost:8000"
	python -m http.server 8000

e2e:
	@echo "Running Playwright E2E (requires deps installed)"
	cd e2e && npm test

pages-links:
	@echo "Generate AB links (set BASE=https://<pages-url>/)"
	@python scripts/ab_links.py --base $${BASE:?BASE is required, e.g. BASE=https://user.github.io/repo/}

check:
	@echo "Checking LP readiness (config.js, files)"
	python3 scripts/check_lp_ready.py || true

# FX helpers (optional)
fx-backtest-sample:
	@echo "Running sample backtest (requires Python + deps)"
	PYTHONPATH=src python -m fxbot.cli backtest \
	  --csv data/sample_USDJPY_1h.csv \
	  --pair USDJPY \
	  --config config/config.yaml \
	  --out out/report_sample.json

fx-export-sample:
	@echo "Exporting sample report CSVs"
	PYTHONPATH=src python -m fxbot.cli report-export \
	  --in out/report_sample.json \
	  --out-dir out/report_sample_csv

fx-help:
	@echo "fxbot CLI help"
	@PYTHONPATH=src python -c "import fxbot.cli as c; p=c.build_parser(); p.print_help()"

fx-optimize-sample:
	@echo "Running sample optimize"
	PYTHONPATH=src python -m fxbot.cli optimize \
	  --csv data/sample_USDJPY_1h.csv \
	  --pair USDJPY \
	  --config config/config.yaml \
	  --ema-fast 10,20,30 \
	  --ema-slow 50,80,120 \
	  --atr-window 10,14,20 \
	  --atr-k 1.5,2.0,2.5 \
	  --atr-min-pct 0.0,0.02,0.03 \
	  --out out/opt_sample.json

fx-walkforward-sample:
	@echo "Running sample walk-forward"
	PYTHONPATH=src python -m fxbot.cli walkforward \
	  --csv data/sample_USDJPY_1h.csv \
	  --pair USDJPY \
	  --config config/config.yaml \
	  --ema-fast 10,20,30 \
	  --ema-slow 50,80,120 \
	  --atr-window 10,14,20 \
	  --atr-k 1.5,2.0,2.5 \
	  --atr-min-pct 0.0,0.02,0.03 \
	  --train-bars 1200 \
	  --test-bars 400 \
	  --out out/wf_sample.json

fx-pipeline-quick:
	@echo "Running pipeline (backtest -> optimize -> best -> export -> WF)"
	python3 scripts/fx_pipeline.py --csv $${CSV:-data/USDJPY_1h.csv} --pair $${PAIR:-USDJPY} --out-dir out/pipeline --train-bars $${TRAIN:-1000} --test-bars $${TEST:-300}

release-notes:
	@echo "--- RELEASE NOTES v0.1.0 ---"
	@sed -n '1,200p' docs/RELEASE_NOTES_v0.1.0.md

release-checklist:
	@echo "--- RELEASE CHECKLIST ---"
	@sed -n '1,200p' docs/RELEASE_CHECKLIST.md
