#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
    echo "This build recipe requires an Apple Silicon Mac." >&2
    exit 1
fi

BUILD_PYTHON="${BUILD_PYTHON:-python3}"
"$BUILD_PYTHON" -c 'import tkinter; import _tkinter' || {
    echo "Python needs Tkinter. For Homebrew Python 3.12: brew install python-tk@3.12" >&2
    exit 1
}
"$BUILD_PYTHON" -m venv .venv-build
.venv-build/bin/python -m pip install -r requirements-build-macos.txt
.venv-build/bin/python -m pytest -q
.venv-build/bin/python -m PyInstaller --clean --noconfirm PreviewCleaner.spec
codesign --verify --deep --strict dist/PreviewCleaner.app
ditto -c -k --sequesterRsrc --keepParent dist/PreviewCleaner.app dist/PreviewCleaner-macOS-arm64.zip
echo "Built: dist/PreviewCleaner.app"
echo "Archive: dist/PreviewCleaner-macOS-arm64.zip"
