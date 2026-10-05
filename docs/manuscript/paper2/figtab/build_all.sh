#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
REPO="$(cd ../../../.. && pwd)"

python3 data/extract_tables.py
python3 data/extract_tables.py --selftest

for f in build_fig_judgement.py build_fig_effects.py build_fig_timeline.py build_fig_synthetic.py \
         build_fig_variants.py build_fig_noise.py build_fig_tradeoff.py; do
  python3 "$f" --selftest
  python3 "$f"
done

python3 build_tables.py --selftest
python3 build_tables.py

python3 build_figtab_docx.py --selftest
python3 build_figtab_docx.py --zip

python3 "$REPO/analysis/scripts/check_terminology.py" docs/manuscript/paper2/figtab
