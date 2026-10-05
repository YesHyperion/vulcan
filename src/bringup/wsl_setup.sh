#!/usr/bin/env bash
# VULCAN - one-shot WSL2 (Ubuntu) host setup. Idempotent: safe to re-run.
#
# Installs the CAN userspace (can-utils) and a Python venv with the core stack.
# Needs sudo for apt -> run this yourself in your Ubuntu terminal (it will prompt
# for your password). Does NOT touch the cluster and does NOT energize anything.
#
# Usage (from the repo, inside WSL Ubuntu):
#   bash src/bringup/wsl_setup.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="$HOME/.venvs/vulcan"   # kept off /mnt/c (Windows FS) for speed & pip sanity

echo "== VULCAN WSL2 setup =="
echo "repo : $REPO_ROOT"
echo "venv : $VENV"

echo "-- apt: can-utils + python venv tooling --"
sudo apt-get update -qq
sudo apt-get install -y can-utils python3-venv python3-pip iproute2

echo "-- python venv + core stack --"
[ -d "$VENV" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip -q
"$VENV/bin/pip" install -q -r "$REPO_ROOT/requirements.txt"

echo
echo "== done =="
echo "can-utils: $(command -v candump || echo MISSING)"
echo "activate the venv with:  source $VENV/bin/activate"
echo "sanity (virtual bus):    bash src/bringup/vcan_up.sh && cangen vcan0 -g 10 &"
echo "                         python src/bringup/sanity_check.py -c vcan0 -t 5"
