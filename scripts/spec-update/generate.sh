#!/usr/bin/env bash
# Codegen for the automated spec-update workflow.
# Runs from the repo root, after Python is set up and submodules are updated.
set -euo pipefail

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install ruff
python generate_base_client.py
ruff format dropbox
ruff check --fix dropbox
