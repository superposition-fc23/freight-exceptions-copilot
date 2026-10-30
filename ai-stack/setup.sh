#!/bin/zsh
# Rebuilds the environment. Run after moving this folder or if imports fail.
set -e
cd "$(dirname "$0")"
UV=$(command -v uv || echo ~/Library/Python/3.9/bin/uv)
$UV sync
# XGBoost needs libomp on macOS; reuse the copy bundled with scikit-learn (no Homebrew needed).
SP=.venv/lib/python3.12/site-packages
cp $SP/sklearn/.dylibs/libomp.dylib $SP/xgboost/lib/
install_name_tool -add_rpath @loader_path $SP/xgboost/lib/libxgboost.dylib 2>/dev/null || true
codesign -f -s - $SP/xgboost/lib/libxgboost.dylib 2>/dev/null
.venv/bin/python rag.py index docs
echo "Ready."
